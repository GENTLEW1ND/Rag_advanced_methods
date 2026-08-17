from typing import TypedDict, List, Annotated
import operator

class AgentStage(TypedDict):
    # Using annotated with operator, add, and ensure the messages
    # are appended to the history rather than replaced.
    messages: Annotated[List[dict], operator.add]
    current_query: str
    documents: List[str]
    plan: List[str]
    status: str
    final_answer: str