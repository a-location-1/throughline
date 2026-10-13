type LogLevel = 'info' | 'warn' | 'error';
type LogContext = Record<string, unknown>;

function write(level: LogLevel, message: string, context: LogContext = {}): void {
  console[level](message, context);
  void fetch('/api/logs', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ level, message, context }),
  }).catch(() => undefined);
}

export const logger = {
  info: (message: string, context?: LogContext) => write('info', message, context),
  warn: (message: string, context?: LogContext) => write('warn', message, context),
  error: (message: string, context?: LogContext) => write('error', message, context),
};