"""
graph.py — Main LangGraph Multi-Agent Topology (SPEC-10)
========================================================
Hub-and-spoke multi-agent graph with Goal Strategist reflection loop,
Goal Auditor (Critic), selective HITL Gatekeeper, and SQLite/PostgreSQL
checkpointer state persistence.
"""
import os
import uuid
from typing import Dict, Any, Optional
from langgraph.graph import START, END, StateGraph
from src.models.state import FinnieState
from src.agents.supervisor import supervisor_node
from src.agents.qa_agent import financial_qa_node
from src.agents.portfolio_analyst import portfolio_analyst_node
from src.agents.compliance import compliance_guardian_node
from src.agents.market_insights import market_insights_node
from src.agents.goal_strategist import goal_strategist_node
from src.agents.goal_auditor import goal_auditor_node
from src.agents.hitl_gatekeeper import hitl_approval_node
from src.database import DATABASE_URL, _LOCAL_DB_PATH
from src.utils.sqlite_saver import SqliteSaver


# 1. Initialize the Graph Builder
workflow = StateGraph(FinnieState)

# 2. Register Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("financial_qa", financial_qa_node)
workflow.add_node("portfolio_analyst", portfolio_analyst_node)
workflow.add_node("market_insights", market_insights_node)
workflow.add_node("goal_strategist", goal_strategist_node)
workflow.add_node("goal_auditor", goal_auditor_node)
workflow.add_node("hitl_approval", hitl_approval_node)
workflow.add_node("compliance", compliance_guardian_node)


# 3. Router Logic
def route_decision(state: FinnieState) -> str:
    """
    Reads the 'next_step' variable to decide which worker to route to.
    """
    step = state.get("next_step")
    if step == "FINANCIAL_QA":
        return "financial_qa"
    elif step == "PORTFOLIO_ANALYST":
        return "portfolio_analyst"
    elif step == "MARKET_INSIGHTS":
        return "market_insights"
    elif step == "GOAL_STRATEGIST":
        return "goal_strategist"
    elif step == "FINISH":
        return "compliance"
    else:
        return "compliance"


def start_node(state: FinnieState) -> str:
    """
    Decides whether to go to supervisor or directly to a specialized worker.
    """
    if state.get("next_step"):
        return route_decision(state)
    return "supervisor"


def route_auditor_decision(state: FinnieState) -> str:
    """
    SPEC-10 Reflection Router:
    - If critic flagged a statutory limit violation: loops back to 'goal_strategist'.
    - If user requested goal lock-in (is_save_intent=True): routes to 'hitl_approval'.
    - Otherwise (exploration complete): routes to 'compliance'.
    """
    if state.get("critic_feedback"):
        return "goal_strategist"
    elif state.get("is_save_intent"):
        return "hitl_approval"
    else:
        return "compliance"


# 4. Wire Edges
workflow.add_conditional_edges(
    START,
    start_node,
    {
        "supervisor": "supervisor",
        "financial_qa": "financial_qa",
        "portfolio_analyst": "portfolio_analyst",
        "market_insights": "market_insights",
        "goal_strategist": "goal_strategist",
        "compliance": "compliance"
    }
)

workflow.add_conditional_edges(
    "supervisor",
    route_decision, 
    {
        "financial_qa": "financial_qa",
        "portfolio_analyst": "portfolio_analyst",
        "market_insights": "market_insights",
        "goal_strategist": "goal_strategist",
        "compliance": "compliance"
    }
)

# Workers route to compliance or critic
workflow.add_edge("financial_qa", "compliance")
workflow.add_edge("portfolio_analyst", "compliance")
workflow.add_edge("market_insights", "compliance")

# SPEC-10 Goal Planning Subgraph
workflow.add_edge("goal_strategist", "goal_auditor")
workflow.add_conditional_edges(
    "goal_auditor",
    route_auditor_decision,
    {
        "goal_strategist": "goal_strategist",
        "hitl_approval": "hitl_approval",
        "compliance": "compliance"
    }
)
workflow.add_edge("hitl_approval", "compliance")

# The only route to END is through compliance
workflow.add_edge("compliance", END)


# 5. Checkpointer Factory & Dual-Mode State Persistence
def get_checkpointer():
    """
    Initializes state checkpointer:
    Uses PostgresSaver when DATABASE_URL is PostgreSQL (Azure cloud),
    otherwise uses colocated SqliteSaver in finnie.db (local/docker).
    """
    db_url = os.environ.get("DATABASE_URL", DATABASE_URL)
    if db_url and db_url.startswith(("postgresql://", "postgres://", "postgresql+psycopg2://")):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            return PostgresSaver.from_conn_string(db_url)
        except Exception as e:
            print(f"[FINNIE-AI] Warning: PostgresSaver unavailable ({e}); falling back to SQLite.")

    db_path = os.environ.get("DB_PATH", _LOCAL_DB_PATH)
    return SqliteSaver(db_path)


checkpointer = get_checkpointer()
_compiled_app = workflow.compile(checkpointer=checkpointer)


class FinnieAppWrapper:
    """
    Backward-compatible wrapper around compiled StateGraph.
    Ensures that invocations without an explicit configurable.thread_id
    automatically receive an ephemeral thread ID rather than failing.
    """

    def __init__(self, app: Any) -> None:
        self._app = app

    def _ensure_config(self, input_state: Any, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        cfg = dict(config or {})
        configurable = dict(cfg.get("configurable", {}))
        if "thread_id" not in configurable:
            tid = None
            if isinstance(input_state, dict):
                tid = input_state.get("trace_id")
                if not tid and input_state.get("user_id"):
                    tid = f"session_{input_state.get('user_id')}"
            configurable["thread_id"] = tid or f"ephemeral_{uuid.uuid4().hex[:12]}"
        cfg["configurable"] = configurable
        return cfg

    async def ainvoke(self, input_state: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        cfg = self._ensure_config(input_state, config)
        return await self._app.ainvoke(input_state, config=cfg, **kwargs)

    def invoke(self, input_state: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        cfg = self._ensure_config(input_state, config)
        return self._app.invoke(input_state, config=cfg, **kwargs)

    async def astream(self, input_state: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        cfg = self._ensure_config(input_state, config)
        async for chunk in self._app.astream(input_state, config=cfg, **kwargs):
            yield chunk

    def astream_events(self, input_state: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        cfg = self._ensure_config(input_state, config)
        return self._app.astream_events(input_state, config=cfg, **kwargs)

    def get_state(self, config: Dict[str, Any]) -> Any:
        return self._app.get_state(config)

    def update_state(self, config: Dict[str, Any], values: Any, as_node: Optional[str] = None) -> Any:
        return self._app.update_state(config, values, as_node=as_node)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._app, name)


finnie_app = FinnieAppWrapper(_compiled_app)
