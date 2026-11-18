-- Script de inicialización para crear la base de datos de pruebas independiente
SELECT 'CREATE DATABASE taskmanager_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'taskmanager_test')\gexec
