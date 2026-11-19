"""Pruebas de aceptación E2E con Selenium validando Frontend, Backend y BD."""

from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import threading
import time
import uuid
from unittest.mock import patch
import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import uvicorn

from app.database import Base, get_db, init_db
from app.main import app
from tests.conftest import TestingSessionLocal, test_engine

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() != "false"


class QuietSPAHandler(SimpleHTTPRequestHandler):
    """Sirve los archivos estáticos de frontend/dist sin ruido en consola."""

    def log_message(self, format: str, *args: object) -> None:  # pylint: disable=W0622
        """Silencia los logs HTTP durante las pruebas E2E."""


def create_webdriver() -> WebDriver:
    """Inicializa Chrome o Edge en modo headless para ejecución local y CI/CD."""
    chrome_options = ChromeOptions()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1440,900")

    try:
        return webdriver.Chrome(options=chrome_options)
    except WebDriverException:
        edge_options = EdgeOptions()
        if HEADLESS:
            edge_options.add_argument("--headless=new")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1440,900")
        return webdriver.Edge(options=edge_options)


def _are_external_services_up() -> bool:
    """Verifica si Frontend y Backend ya están corriendo (por ejemplo en Docker)."""
    try:
        backend_res = requests.get(f"{BACKEND_URL}/health", timeout=1)
        frontend_res = requests.get(FRONTEND_URL, timeout=1)
        return backend_res.status_code == 200 and frontend_res.status_code == 200
    except requests.RequestException:
        return False


@contextmanager
def _ensure_e2e_stack() -> Generator[None, None, None]:
    """Usa los contenedores activos o levanta servidores locales para E2E."""
    if _are_external_services_up():
        yield
        return

    dist_dir = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if not dist_dir.exists():
        pytest.skip(
            "No se encontró frontend/dist ni servicios en ejecución. "
            "Ejecuta 'docker compose up -d' o 'cd frontend && npm run build'."
        )

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[object, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.main.init_db",
        side_effect=lambda: init_db(db_engine=test_engine),
    ):
        uv_config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="error",
        )
        uv_server = uvicorn.Server(uv_config)
        backend_thread = threading.Thread(target=uv_server.run, daemon=True)
        backend_thread.start()

        handler = partial(QuietSPAHandler, directory=str(dist_dir))
        frontend_server = ThreadingHTTPServer(("127.0.0.1", 3000), handler)
        frontend_thread = threading.Thread(
            target=frontend_server.serve_forever,
            daemon=True,
        )
        frontend_thread.start()

        for _ in range(50):
            if _are_external_services_up():
                break
            time.sleep(0.1)

        try:
            yield
        finally:
            frontend_server.shutdown()
            frontend_server.server_close()
            uv_server.should_exit = True
            backend_thread.join(timeout=3)
            frontend_thread.join(timeout=3)
            app.dependency_overrides.clear()
            Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def driver() -> Generator[WebDriver, None, None]:
    """Provee una instancia de navegador Selenium conectada al stack E2E."""
    with _ensure_e2e_stack():
        browser = create_webdriver()
        try:
            yield browser
        finally:
            browser.quit()


def _fill_and_submit_task_form(
    driver: WebDriver,
    wait: WebDriverWait,
    title: str,
    description: str,
) -> None:
    """Rellena y envía el formulario de creación o edición de tarea."""
    title_input = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[data-testid='task-title-input']")
        )
    )
    desc_input = driver.find_element(
        By.CSS_SELECTOR, "[data-testid='task-description-input']"
    )
    submit_btn = driver.find_element(
        By.CSS_SELECTOR, "[data-testid='task-submit-button']"
    )
    title_input.clear()
    title_input.send_keys(title)
    desc_input.clear()
    desc_input.send_keys(description)
    submit_btn.click()


def _assert_backend_task(
    task_id: int,
    expected_title: str,
    expected_description: str,
    expected_status: str,
) -> None:
    """Verifica en la API REST que el estado en la base de datos coincida con la UI."""
    response = requests.get(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=5)
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == expected_title
    assert payload["description"] == expected_description
    assert payload["status"] == expected_status


def _verify_filters_and_delete_task(
    driver: WebDriver,
    wait: WebDriverWait,
    task_id: int,
) -> None:
    """Verifica el filtrado por estados y la eliminación con confirmación."""
    card_selector = f"article[data-task-id='{task_id}']"

    driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-Pending']").click()
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, card_selector)))

    driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-Completed']").click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, card_selector)))

    driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-all']").click()
    target_card = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, card_selector))
    )

    target_card.find_element(By.CSS_SELECTOR, "[data-testid='task-delete-btn']").click()

    confirm_modal = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='confirm-modal']")
        )
    )
    confirm_modal.find_element(
        By.CSS_SELECTOR, "[data-testid='confirm-delete-btn']"
    ).click()

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, card_selector)))
    api_deleted = requests.get(f"{BACKEND_URL}/api/tasks/{task_id}", timeout=5)
    assert api_deleted.status_code == 404


@pytest.mark.acceptance
def test_selenium_complete_task_manager_workflow(driver: WebDriver) -> None:
    """
    Escenario completo de aceptación con Selenium que valida los 7 puntos requeridos:
    1. Carga correcta de la aplicación.
    2. Creación de una tarea.
    3. Visualización de la tarea.
    4. Edición de la información.
    5. Cambio de estado.
    6. Filtrado de tareas.
    7. Eliminación de una tarea.
    """
    wait = WebDriverWait(driver, 15)
    suffix = uuid.uuid4().hex[:6]
    initial_title = f"Tarea Selenium {suffix}"
    initial_desc = f"Descripción inicial E2E {suffix}"
    edited_title = f"Tarea Selenium Editada {suffix}"
    edited_desc = f"Descripción actualizada E2E {suffix}"

    # 1. Carga correcta de la aplicación
    driver.get(FRONTEND_URL)
    header = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='app-header']")
        )
    )
    assert "Task Manager" in header.text
    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "[data-testid='stat-total']")
        )
    )

    # 2. Creación de una tarea y 3. Visualización en UI + Backend
    _fill_and_submit_task_form(driver, wait, initial_title, initial_desc)

    task_card = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//article[@data-testid='task-card' and "
                f".//*[@data-testid='task-title' and "
                f"contains(text(), '{initial_title}')]]",
            )
        )
    )
    task_id = int(task_card.get_attribute("data-task-id") or "0")
    assert task_id > 0
    assert initial_desc in task_card.text
    _assert_backend_task(task_id, initial_title, initial_desc, "Pending")

    # 4. Edición de la información
    task_card.find_element(By.CSS_SELECTOR, "[data-testid='task-edit-btn']").click()
    _fill_and_submit_task_form(driver, wait, edited_title, edited_desc)

    edited_card = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//article[@data-testid='task-card' and "
                f"@data-task-id='{task_id}' and "
                f".//*[@data-testid='task-title' and "
                f"contains(text(), '{edited_title}')]]",
            )
        )
    )
    assert edited_desc in edited_card.text
    _assert_backend_task(task_id, edited_title, edited_desc, "Pending")

    # 5. Cambio de estado (Pending -> Completed)
    edited_card.find_element(
        By.CSS_SELECTOR, "[data-testid='task-toggle-status-btn']"
    ).click()

    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//article[@data-testid='task-card' and "
                f"@data-task-id='{task_id}']"
                f"//*[@data-testid='task-status-badge' and "
                f"@data-status='Completed']",
            )
        )
    )
    _assert_backend_task(task_id, edited_title, edited_desc, "Completed")

    # 6. Filtrado y 7. Eliminación con confirmación
    _verify_filters_and_delete_task(driver, wait, task_id)
