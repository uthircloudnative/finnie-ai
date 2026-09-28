import contextvars
import logging
import uuid
import time
from typing import Dict, Any, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Context variable for request-scoped trace ID
trace_id_var = contextvars.ContextVar("trace_id", default=None)

# Context variable for counting real LLM calls made during the active request
llm_call_counter_var = contextvars.ContextVar("llm_call_counter", default=0)


def get_llm_call_count() -> int:
    """Returns the total number of real LLM calls executed during the current request."""
    return llm_call_counter_var.get()


def reset_llm_call_count() -> None:
    """Resets the request-scoped LLM call counter."""
    llm_call_counter_var.set(0)


class ConsoleTelemetryCallbackHandler(BaseCallbackHandler):
    """
    Standard LangChain callback handler that intercepts and logs real LLM invocations,
    latencies, and token metrics in real time across any agent node without modifying node code.
    """
    def __init__(self):
        super().__init__()
        self._start_times: Dict[str, float] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: Any = None, **kwargs: Any
    ) -> None:
        key = str(run_id) if run_id else "default"
        self._start_times[key] = time.time()

    def on_llm_end(self, response: LLMResult, *, run_id: Any = None, **kwargs: Any) -> None:
        key = str(run_id) if run_id else "default"
        elapsed = time.time() - self._start_times.pop(key, time.time())
        current_count = llm_call_counter_var.get() + 1
        llm_call_counter_var.set(current_count)

        llm_output = response.llm_output or {}
        model_name = llm_output.get("model_name", "OpenAI / LLM")
        token_usage = llm_output.get("token_usage", {})
        tokens_info = f" | Total Tokens={token_usage.get('total_tokens', 'N/A')}" if token_usage else ""

        tid = trace_id_var.get()
        short_tid = f" [Trace-{tid[:8]}]" if tid else ""
        print(
            f"[FINNIE-AI]{short_tid} 🧠 [REAL LLM CALL #{current_count}] "
            f"Model='{model_name}' | Elapsed={elapsed:.2f}s{tokens_info}"
        )

    def on_llm_error(self, error: BaseException, *, run_id: Any = None, **kwargs: Any) -> None:
        key = str(run_id) if run_id else "default"
        elapsed = time.time() - self._start_times.pop(key, time.time())
        tid = trace_id_var.get()
        short_tid = f" [Trace-{tid[:8]}]" if tid else ""
        print(
            f"[FINNIE-AI]{short_tid} ❌ [LLM CALL FAILED] Error: {error} | Elapsed={elapsed:.2f}s"
        )


def get_graph_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Standard LangGraph runtime config factory injecting:
      1. Centralized ConsoleTelemetryCallbackHandler for real LLM call telemetry.
      2. LangSmith distributed trace metadata (app_trace_id).
      3. Thread persistence configuration when applicable.
    """
    tid = trace_id_var.get()
    cfg: Dict[str, Any] = {
        "callbacks": [ConsoleTelemetryCallbackHandler()],
        "metadata": {"app_trace_id": tid} if tid else {}
    }
    if thread_id:
        cfg["configurable"] = {"thread_id": thread_id}
    return cfg


def record_llm_call(node_name: str, model_name: str, elapsed_seconds: float, prompt_chars: int = 0, response_chars: int = 0) -> int:
    """
    Backwards-compatible helper for explicit telemetry logging if ever invoked directly.
    """
    current_count = llm_call_counter_var.get() + 1
    llm_call_counter_var.set(current_count)
    tid = trace_id_var.get()
    short_tid = f" [Trace-{tid[:8]}]" if tid else ""
    print(
        f"[FINNIE-AI]{short_tid} 🧠 [REAL LLM CALL #{current_count}] "
        f"Node='{node_name}' | Model='{model_name}' | "
        f"Elapsed={elapsed_seconds:.2f}s | Prompt={prompt_chars} chars | Response={response_chars} chars"
    )
    return current_count


class TraceContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware that generates a unique trace ID and resets the LLM call counter
    for incoming requests, making telemetry accessible across the request lifecycle.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = uuid.uuid4().hex
        token_tid = trace_id_var.set(trace_id)
        token_llm = llm_call_counter_var.set(0)

        t_start = time.time()
        method = request.method
        path = request.url.path

        # Filter API paths for clean logging
        is_api_call = path.startswith(("/goals", "/chat", "/portfolio", "/market", "/dashboard", "/auth"))

        if is_api_call:
            print(f"\n[FINNIE-AI] [Trace-{trace_id[:8]}] 🌐 ---> INCOMING UI REQUEST: {method} {path}")

        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-LLM-Calls"] = str(get_llm_call_count())

            if is_api_call:
                elapsed = time.time() - t_start
                total_llm = get_llm_call_count()
                print(
                    f"[FINNIE-AI] [Trace-{trace_id[:8]}] 🏁 <--- COMPLETED: {method} {path} "
                    f"in {elapsed:.2f}s (HTTP {response.status_code}) | Total Real LLM Calls: {total_llm}\n"
                )
            return response
        finally:
            trace_id_var.reset(token_tid)
            llm_call_counter_var.reset(token_llm)


class TraceAwareFormatter(logging.Formatter):
    """
    Custom Logger Formatter that extracts current trace_id and injects it into logs.
    """
    def format(self, record: logging.LogRecord) -> str:
        trace_id = trace_id_var.get()
        if trace_id:
            record.msg = f"[Trace-{trace_id[:8]}] {record.msg}"
        return super().format(record)


def setup_telemetry_logging():
    """
    Overrides the default Python root logger to use TraceAwareFormatter.
    """
    handler = logging.StreamHandler()
    formatter = TraceAwareFormatter('%(levelname)s:     %(message)s')
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
