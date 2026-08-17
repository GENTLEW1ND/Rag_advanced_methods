from app.agents.state import AgentStage
from app.config import settings
from langchain_groq import ChatGroq
import logfire

# Direct Groq call - the LLM Gatway (Portkey routing/fallback/) arrives in a
llm = ChatGroq(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL, temperature = 0)


def planner_node(state: AgentStage):
    """
    The planner determines if a search is needed based on the Entire Conversation.
    """
    
    # Get the Conversation hisstory (excluding the latest message)
    
    history = ""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history += f"{role}: {msg['content']}\n"
        
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    
    prompt = f"""
    You are a intelligent Assistant Planner.
    Analyse the Conversation history and the latest user message.
    
    CONVERSATION HISTORY:
    {history}
    
    LATEST MESSAGE:
    "{user_message}"
    
    Task:
    1. If the latest message is a greeting (hi, hello) or a question that can be answered
    using ONLY the conversation history above (e.g., "what is my name"), respond with 'CONVERSATIONAL'
    
    2. If it is a technical question about Kubernates, Intel, or Networking that requires fresh documentation,
    output a refined search query.
    
    Output ONLY 'CONVERSATIONAL' or the search query.
    """
    
    with logfire.span("Planner Decision"):
        decision = llm.invoke(prompt).content.strip()
        logfire.info(f"Intent indentified: {decision}")
        
    if decision == "CONVERSATIONAL":
        return {
            "current_query": "CONVERSATIONAL",
            "status": "Handline conversationally (using memory)...",
            "plan": ["Intent: Conversational/Memory", "Retrival: Skipped"]
        }
        
    return{
        "current_query": decision,
        "status": f"Technical research needed. Searching for: {decision}",
        "plan": ["Intent: Technical", f"Search Term: {decision}"] 
    }