/**
 * Logger utility for frontend application.
 * In development, logs to console. In production, can be extended to send to error tracking service.
 */

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
  error: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.error(...args);
    }
    // In production, you could send to error tracking service (e.g., Sentry)
    // Example: Sentry.captureException(new Error(String(args[0])));
  },
  warn: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.warn(...args);
    }
  },
  info: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.info(...args);
    }
  },
  debug: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.debug(...args);
    }
  },
};

