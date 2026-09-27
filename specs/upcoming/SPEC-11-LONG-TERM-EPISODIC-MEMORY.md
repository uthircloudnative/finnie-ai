# Feature Spec: SPEC-11 — Cross-Session Long-Term Episodic Memory & Knowledge Graph

> **Status**: ⚪ **PROPOSED / FUTURE ROADMAP (PHASE 9)**  
> **Author**: Antigravity & Lead Engineer  
> **Scope**: Backend, Mem0, LangGraph Store, Knowledge Graph, Multi-Tenancy, Azure Cloud  
> **Target Release**: v0.9.0 (Phase 9)  
> **Prerequisite**: SPEC-10 (Production In-Session Memory & Checkpointing)

---

## 1. 🎯 Business Objective & Domain Rules

### Problem Statement
Currently, each user interaction with Finnie AI is confined to its active session. While **SPEC-10** provides in-session thread continuity for the Goal Strategist, the agent still suffers from **cross-session and cross-tab amnesia**:
1. When a user discusses their family context (*"I have 2 kids, ages 4 and 7"*), risk appetite (*"I refuse to invest in crypto"*), or tax residency (*"I live in Texas"*) in the Live Chat, the other agents (Portfolio Analyst, Goal Strategist) have zero access to this context.
2. When the user logs out and logs back in weeks later, Finnie cannot reference previous conversations or life events.

### Domain Rules & Invariants
- **Autonomous Memory Extraction**: An in-process memory engine (Mem0) automatically analyzes user utterances across sessions to extract structured facts, life milestones, and preferences.
- **Contradiction & Temporal Resolution**: If a user updates a fact (e.g. salary increases from $120k to $145k, or retirement target shifts from 65 to 58), the memory engine updates the fact rather than holding contradictory entries.
- **Strict Multi-Tenant Security (Golden Rule #1)**:
  - All memories are strictly namespaced by `user_id = current_user.id`.
  - Zero cross-contamination between tenant memory stores.
- **Regulatory & Privacy Rules**:
  - PII masking applied prior to memory indexing.
  - Compliance footer (`$NFA`) remains mandatory across all memory-augmented outputs.

---

## 2. 🔌 Technical Contracts & Architecture

### A. Memory Engine Selection: Mem0 (Embedded Mode with Graph Memory)
- **Engine**: `mem0ai` running in-process inside FastAPI.
- **Storage**: Backed by primary database (`finnie.db` in SQLite for local dev, PostgreSQL for Azure) with vector storage in ChromaDB or `pgvector`.
- **Graph Memory Extension**: Extracts entity-relationship paths:
  `(User) -[:HAS_GOAL]-> (Retirement 2045) -[:ALLOCATED_TO]-> (Index Funds)`.

### B. Memory Tool Manifest (`backend/src/tools/memory_tools.py`)
```python
@tool
def save_user_memory(fact: str, category: str = "preference") -> str:
    """Saves a permanent fact, preference, or life milestone for this user."""

@tool
def recall_user_memories(query: str) -> list[str]:
    """Retrieves relevant facts and past discussions for the active user."""
```

### C. System Boot Context Injection
On any authenticated endpoint or graph invocation, the supervisor or agent retrieves the user's top profile facts:
```python
user_memories = memory_service.get_user_profile(user_id=effective_id)
# Injected into state["memory_context"] and state["user_profile"]
```

---

## 3. ☁️ Production Azure Deployment Readiness
- Runs in-process within the FastAPI container without requiring an external microservice cluster.
- Reuses the existing PostgreSQL connection pool in Azure.
- Zero extra monthly hosting cost compared to dedicated memory services.

---

## 4. ✅ Acceptance Criteria & Test Plan
- [ ] **AC-1**: Stating an investment preference in Chat updates the user's memory store.
- [ ] **AC-2**: Starting a new Goal Planner session weeks later automatically incorporates that preference into recommendations.
- [ ] **AC-3**: Updating a conflicting fact (e.g. new target year) resolves the conflict in favor of the newer statement.
- [ ] **AC-4**: Multi-tenant isolation verified: User B cannot retrieve or observe User A's memories.
