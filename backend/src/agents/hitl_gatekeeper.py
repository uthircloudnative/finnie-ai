"""
hitl_gatekeeper.py — Human-in-the-Loop Node for Strategy Lock-In (SPEC-10)
==========================================================================
Invokes LangGraph interrupt() when the user commits to locking in and saving their
goal strategy. Resumes upon explicit user confirmation, persisting to financial_goals.
"""
from typing import Dict, Any
from langgraph.types import interrupt
from langchain_core.messages import AIMessage
from src.models.state import FinnieState
from src.database import SessionLocal
from src.models.goal import FinancialGoal


def hitl_approval_node(state: FinnieState) -> Dict[str, Any]:
    """
    Selective HITL gatekeeper node.
    Halts execution and yields control to the user only when is_save_intent is True.
    Persists to financial_goals upon confirmation.
    """
    print("[FINNIE-AI] 🛡️ Entering HITL Gatekeeper Node (Deterministic Checkpoint, 0 LLM calls)...")
    config = state.get("goal_configuration") or {}
    analysis = state.get("analysis_results") or {}
    sim_data = analysis.get("simulation") or {}
    user_id = state.get("user_id") or config.get("user_id")
    goal_name = config.get("goal_name", "Retirement")
    target_amount = float(config.get("target_amount", 1000000.0))
    target_year = int(config.get("target_year", 2035))
    monthly_savings = float(config.get("monthly_savings", 500.0))
    country = str(config.get("country", "USA"))
    confidence = float(sim_data.get("confidence_score", 0.0))
    messages = state.get("messages") or []

    # Get last AI roadmap report
    report = ""
    for m in reversed(messages):
        if hasattr(m, "type") and m.type == "ai":
            report = m.content
            break

    # If saving is requested, trigger interrupt to pause and await explicit user sign-off
    if state.get("is_save_intent"):
        print(f"[FINNIE-AI] ⏸️ Triggering interrupt() for goal '{goal_name}' lock-in...")
        decision = interrupt({
            "type": "CONFIRM_STRATEGY",
            "goal_name": goal_name,
            "target_amount": target_amount,
            "target_year": target_year,
            "monthly_savings": monthly_savings,
            "confidence_score": confidence,
            "country": country
        })

        # Resumed from interrupt with decision dict
        if decision and decision.get("approved"):
            print(f"[FINNIE-AI] ✅ User confirmed lock-in for '{goal_name}'. Persisting to database...")
            db = SessionLocal()
            try:
                goal = db.query(FinancialGoal).filter(
                    FinancialGoal.user_id == user_id,
                    FinancialGoal.goal_name == goal_name
                ).first()

                assigned_thread = decision.get("thread_id") or config.get("thread_id") or f"goal_{user_id}_{goal_name.lower().replace(' ', '_')}"

                if not goal:
                    goal = FinancialGoal(
                        user_id=user_id,
                        goal_name=goal_name,
                        target_amount=target_amount,
                        target_year=target_year,
                        monthly_contribution=monthly_savings,
                        country=country,
                        thread_id=assigned_thread,
                        status="LOCKED",
                        confidence_score=confidence,
                        strategy_report=report
                    )
                    db.add(goal)
                else:
                    goal.target_amount = target_amount
                    goal.target_year = target_year
                    goal.monthly_contribution = monthly_savings
                    goal.country = country
                    goal.thread_id = assigned_thread
                    goal.status = "LOCKED"
                    goal.confidence_score = confidence
                    goal.strategy_report = report

                db.commit()
                db.refresh(goal)
                confirm_msg = (
                    f"🎉 **Strategy Locked & Saved!** Your **{goal_name}** roadmap is now permanently locked "
                    f"with a target of ${target_amount:,.0f} by {target_year} and an audited confidence score of {confidence:.1f}%."
                )
                return {
                    "messages": [AIMessage(content=confirm_msg)],
                    "is_save_intent": False
                }
            except Exception as e:
                db.rollback()
                print(f"[FINNIE-AI] ❌ Database error saving goal: {e}")
                err_msg = f"⚠️ Could not lock in goal due to a storage error: {e}"
                return {
                    "messages": [AIMessage(content=err_msg)],
                    "is_save_intent": False
                }
            finally:
                db.close()

    return {"is_save_intent": False}
