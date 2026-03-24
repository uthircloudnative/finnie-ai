
from langgraph.graph import START, END, StateGraph
from src.models.state import FinnieState
from src.agents.supervisor import supervisor_node
from src.agents.qa_agent import financial_qa_node


# 1. Initialize the Graph Builder using our Pydantic State Object
from langgraph.constants import END
workflow = StateGraph(FinnieState)

# 2. Add our "Nodes" (The Worker Functions)
workflow.add_node("supervisor",supervisor_node)
workflow.add_node("financial_qa",financial_qa_node)

# 3. Define the Router Logic
def route_decision(state: FinnieState) -> str:
    """
    Reads the 'next_step' variable to decide which edge to take.
    """

    step = state.get("next_step")
    if step == "FINANCIAL_QA":
        return "financial_qa"
    elif step == "FINISH":
        return END
    else:
        return END

# 4. Wiring the Edges (The Flow)
# The conversation always starts at the Supervisor
workflow.add_edge(START, "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_decision, 
    {
        "financial_qa": "financial_qa",
        END: END
    }
)

# After the Q&A worker finishes answering, we wrap up the conversation
workflow.add_edge("financial_qa",END)

# 5. Compile the graph into a runnable application!
finnie_app = workflow.compile()



