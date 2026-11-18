import React from 'react';

export interface AlertState {
  type: 'success' | 'error';
  message: string;
}

interface AlertBannerProps {
  alert: AlertState | null;
  onDismiss: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alert, onDismiss }) => {
  if (!alert) {
    return null;
  }

  return (
    <div
      className={`alert-banner alert-${alert.type}`}
      role={alert.type === 'error' ? 'alert' : 'status'}
      data-testid="alert-banner"
      data-alert-type={alert.type}
    >
      <span className="alert-text">{alert.message}</span>
      <button
        type="button"
        className="alert-close-btn"
        onClick={onDismiss}
        aria-label="Cerrar notificación"
        data-testid="alert-close-btn"
      >
        ×
      </button>
    </div>
  );
};
