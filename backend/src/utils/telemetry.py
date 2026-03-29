import contextvars
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# The variable that will hold the trace ID for the current async task
trace_id_var = contextvars.ContextVar("trace_id", default=None)

class TraceContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware that generates a unique trace ID for incoming requests 
    and sets it in the ContextVars so it's globally accessible for the lifecycle of that request.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = uuid.uuid4().hex
        
        # Give life to the trace_id within the context of this async task
        token = trace_id_var.set(trace_id)
        
        try:
            response = await call_next(request)
            # Inject the trace ID into the HTTP response headers for debugging if needed
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            trace_id_var.reset(token)

class TraceAwareFormatter(logging.Formatter):
    """
    Custom Logger Formatter that extracts the current trace_id from ContextVars 
    and injects it into every standard python print/log.
    """
    def format(self, record: logging.LogRecord) -> str:
        trace_id = trace_id_var.get()
        if trace_id:
            record.msg = f"[Trace-{trace_id[:8]}] {record.msg}"
        return super().format(record)

def setup_telemetry_logging():
    """
    Overrides the default Python root logger to use our TraceAwareFormatter.
    Call this once when FastAPI boots.
    """
    handler = logging.StreamHandler()
    formatter = TraceAwareFormatter('%(levelname)s:     %(message)s')
    handler.setFormatter(formatter)

    # Set up root logger
    root_logger = logging.getLogger()
    
    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
