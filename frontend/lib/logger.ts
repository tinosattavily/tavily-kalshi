const isDevelopment = process.env.NODE_ENV === "development";

interface Logger {
  error: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
  debug: (...args: unknown[]) => void;
}

export const logger: Logger = {
  error(...args: unknown[]): void {
    if (isDevelopment) {
      console.error(...args);
    }
  },
  warn(...args: unknown[]): void {
    if (isDevelopment) {
      console.warn(...args);
    }
  },
  info(...args: unknown[]): void {
    if (isDevelopment) {
      console.info(...args);
    }
  },
  debug(...args: unknown[]): void {
    if (isDevelopment) {
      console.debug(...args);
    }
  },
};

