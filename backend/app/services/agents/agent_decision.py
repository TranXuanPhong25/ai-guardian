import json
from typing import Dict, List, Optional, Any, Literal, TypedDict, Union, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import MessagesState, StateGraph, END
import os, getpass
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

from app.config import Config
from app.services.agents.rag_agent import DocumentRAG

load_dotenv()

# Load configuration
config = Config()

# Initialize memory
memory = MemorySaver()

# Specify a thread
thread_config = {"configurable": {"thread_id": "1"}}

# Agent configuration
class AgentConfig:
    """Configuration settings for the agent decision system."""
    
    DECISION_MODEL = "gpt-4o"  # or whichever model you prefer
    CONFIDENCE_THRESHOLD = 0.55
    
    DECISION_SYSTEM_PROMPT = """You are an intelligent routing system that routes user queries to 
    the appropriate specialized agent. Your job is to analyze the user's request and determine which agent 
    is best suited to handle it based on the query content and conversation context.

    Available agents:
    1. CONVERSATION_AGENT - For general chat, greetings, casual questions, current events, weather, news, general knowledge, and real-time information.
    2. RAG_AGENT - For specific factual questions about people, companies, data, statistics, or detailed information that would be found in documents.

    Make your decision based on these guidelines:

    **Use CONVERSATION_AGENT for:**
    - Greetings and casual conversation ("Hello", "How are you?")
    - Weather and current events ("What's the weather today?", "Latest news")
    - General knowledge questions ("What is Python?", "How does photosynthesis work?")
    - Real-time information requests
    - Opinions, advice, or subjective questions
    - Technical explanations that don't require specific data

    **Use RAG_AGENT for:**
    - Specific questions about named individuals ("What is Rebecca Hill's income in 2022?")
    - Company-specific information ("What are XYZ Corp's financial results?")
    - Detailed statistics or data points from documents
    - Questions about specific procedures, policies, or documentation
    - Queries that ask for exact figures, dates, or specific facts
    - Questions that reference specific documents or sources

    **Key indicators for RAG_AGENT:**
    - Questions containing specific names of people, companies, or entities
    - Requests for exact numbers, dates, or statistics
    - Questions asking "What is [specific person's] [specific attribute]?"
    - Queries about specific policies, procedures, or documented information

    **Examples:**

    CONVERSATION_AGENT examples:
    - "Hello, how are you?" → General greeting
    - "What's the weather today?" → Real-time information request
    - "How does machine learning work?" → General knowledge
    - "Can you help me understand Python?" → General technical explanation
    - "What's the latest news?" → Current events

    RAG_AGENT examples:
    - "What is Rebecca Hill's income in 2022?" → Specific person + specific data
    - "What are Apple's quarterly earnings for Q3?" → Company + specific statistics
    - "What is John Smith's role in the marketing department?" → Specific person + specific information
    - "Show me the policy for remote work" → Specific documented information
    - "What was the revenue of XYZ Corp last year?" → Company + specific financial data

    You must provide your answer in JSON format with the following structure:
    {{
    "agent": "AGENT_NAME",
    "reasoning": "Your step-by-step reasoning for selecting this agent",
    "confidence": 0.95  // Value between 0.0 and 1.0 indicating your confidence in this decision
    }}
    """

class AgentState(MessagesState):
    """State maintained across the workflow."""
    agent_name: Optional[str]
    current_input: Optional[Union[str, Dict]]
    output: Optional[str]
    retrieval_confidence: float
    bypass_routing: bool
    insufficient_info: bool

class AgentDecision(TypedDict):
    """Output structure for the decision agent."""
    agent: str
    reasoning: str
    confidence: float

def create_agent_graph():
    """Create and configure the LangGraph for agent orchestration."""
    decision_model = config.conversation.llm
    json_parser = JsonOutputParser()
    
    decision_prompt = ChatPromptTemplate.from_messages([
        ("system", AgentConfig.DECISION_SYSTEM_PROMPT),
        ("human", "{input}")
    ])
    
    decision_chain = decision_prompt | decision_model | json_parser

    def analyze_input(state: AgentState) -> AgentState:
        """Analyze the input."""
        return {
            **state,
            "bypass_routing": False
        }
    
    def route_to_agent(state: AgentState) -> AgentState:
        """Make decision about which agent should handle the query."""
        messages = state["messages"]
        current_input = state["current_input"]
        
        input_text = ""
        if isinstance(current_input, str):
            input_text = current_input
        elif isinstance(current_input, dict):
            input_text = current_input.get("text", "")
        
        recent_context = ""
        for msg in messages[-6:]:
            if isinstance(msg, HumanMessage):
                recent_context += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                recent_context += f"Assistant: {msg.content}\n"
        
        decision_input = f"""
        User query: {input_text}

        Recent conversation context:
        {recent_context}

        Based on this information, which agent should handle this query?
        """
        
        try:
            decision = decision_chain.invoke({"input": decision_input})
            print(f"Decision: {decision['agent']}")
            
            if decision["confidence"] < AgentConfig.CONFIDENCE_THRESHOLD:
                agent_name = "CONVERSATION_AGENT"
            else:
                agent_name = decision["agent"]
                
            return {
                **state,
                "agent_name": agent_name
            }
        except Exception as e:
            print(f"Error in routing decision: {e}")
            return {
                **state,
                "agent_name": "CONVERSATION_AGENT"
            }
    
    def run_conversation_agent(state: AgentState) -> AgentState:
        """Handle general conversation queries."""
        print(f"Selected agent: CONVERSATION_AGENT")
        
        conversation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful conversational AI. Provide accurate and concise answers to the user's query. For example:
            
            **User:** "Hello, how are you?"
            **You:** "I'm doing great, thanks for asking! How about you?"
            
            **User:** "What's the weather like today?"
            **You:** "I don't have real-time weather data, but I can help with general information or suggest checking a weather app or an assistant with internet access for current weather conditions."
            
            **User:** "I need information about a specific topic."
            **You:** "I'd be happy to help! Could you provide more details about what specific information you're looking for?"
            """),
            ("human", "{input}")
        ])
        
        messages = state["messages"]
        query = state["current_input"]
        
        if isinstance(query, dict):
            input_text = query.get("text", "")
        else:
            input_text = query
        
        response = config.conversation.llm.invoke(conversation_prompt.format_messages(input=input_text))
        
        return {
            **state,
            "output": response.content,
            "agent_name": "CONVERSATION_AGENT"
        }
    
    def run_rag_agent(state: AgentState) -> AgentState:
        """Handle document-based queries using RAG."""
        print(f"Selected agent: RAG_AGENT")
        
        rag_agent = DocumentRAG(config)
        
        try:
            messages = state["messages"]
            query = state["current_input"]
            rag_context_limit = config.rag.context_limit
            
            recent_context = ""
            for msg in messages[-rag_context_limit:]:
                if isinstance(msg, HumanMessage):
                    recent_context += f"User: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    recent_context += f"Assistant: {msg.content}\n"
            
            response = rag_agent.process_query(query, chat_history=recent_context)
            retrieval_confidence = response.get("confidence", 0.0)
            
            print(f"Retrieval Confidence: {retrieval_confidence}")
            
            # Đơn giản hóa xử lý response: giả sử response luôn là chuỗi văn bản
            response_text = response["response"]
            
            # Weaviate trả về distance (thấp hơn = tốt hơn), chuyển đổi thành confidence
            # Giả sử confidence cần scale từ distance (0-2) sang 0-1, với distance thấp là confidence cao
            normalized_confidence = max(0.0, 1.0 - (retrieval_confidence / 2.0))
            
            insufficient_info = normalized_confidence < config.rag.min_retrieval_confidence
            
            print(f"Normalized Confidence: {normalized_confidence}")
            print(f"Insufficient info flag set to: {insufficient_info}")
            
            if not insufficient_info:
                response_output = AIMessage(content=response_text)
                print("Using RAG response due to sufficient confidence")
            else:
                response_output = AIMessage(content="Tôi không có đủ thông tin đáng tin cậy để trả lời câu hỏi này một cách chính xác. Vui lòng thử diễn đạt lại câu hỏi hoặc cung cấp thêm ngữ cảnh.")
                print("Using fallback response due to low confidence")
            
            return {
                **state,
                "output": response_output,
                "retrieval_confidence": normalized_confidence,
                "agent_name": "RAG_AGENT",
                "insufficient_info": insufficient_info
            }
        
        finally:
            # Always close the RAG agent connection
            rag_agent.close()
    
    def decide_next_agent(state: AgentState) -> str:
        """Decide which agent to route to based on the decision made."""
        agent_name = state.get("agent_name", "CONVERSATION_AGENT")
        return agent_name
    
    def process_output(state: AgentState) -> AgentState:
        """Process the generated response."""
        output = state["output"]
        
        if not output or not isinstance(output, (str, AIMessage)):
            return state
        
        output_text = output if isinstance(output, str) else output.content
        
        final_message = AIMessage(content=output_text) if isinstance(output, AIMessage) else output_text
        
        return {
            **state,
            "messages": final_message,
            "output": final_message
        }
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("analyze_input", analyze_input)
    workflow.add_node("route_to_agent", route_to_agent)
    workflow.add_node("run_conversation_agent", run_conversation_agent)
    workflow.add_node("run_rag_agent", run_rag_agent)
    workflow.add_node("process_output", process_output)
    
    workflow.set_entry_point("analyze_input")
    workflow.add_edge("analyze_input", "route_to_agent")
    
    workflow.add_conditional_edges(
        "route_to_agent",
        decide_next_agent,
        {
            "CONVERSATION_AGENT": "run_conversation_agent",
            "RAG_AGENT": "run_rag_agent"
        }
    )
    
    workflow.add_edge("run_conversation_agent", "process_output")
    workflow.add_edge("run_rag_agent", "process_output")
    workflow.add_edge("process_output", END)
    
    return workflow.compile(checkpointer=memory)

def init_agent_state() -> AgentState:
    """Initialize the agent state with default values."""
    return {
        "messages": [],
        "agent_name": None,
        "current_input": None,
        "output": None,
        "retrieval_confidence": 0.0,
        "bypass_routing": False,
        "insufficient_info": False
    }

def process_query(query: Union[str, Dict]) -> str:
    """
    Process a user query through the agent decision system.

    Args:
        query: User input (text string or dict with text)

    Returns:
        Response from the appropriate agent
    """
    graph = create_agent_graph()
    state = init_agent_state()
    
    if isinstance(query, dict):
        query_text = query.get("text", "")
    else:
        query_text = query
    
    if query_text:
        rewrite_prompt = f"""Vui lòng viết lại truy vấn sau bằng tiếng Anh đơn giản, rõ ràng, giữ nguyên ý nghĩa và ý định ban đầu:

        Truy vấn gốc: {query_text}

        Truy vấn viết lại:"""
        
        rewritten_query = config.conversation.llm.invoke(rewrite_prompt)
        
        if isinstance(query, dict):
            query["text"] = rewritten_query.content
        else:
            query = rewritten_query.content
    
    state["current_input"] = query
    display_text = query_text if query_text else str(query)
    state["messages"] = [HumanMessage(content=display_text)]
    
    result = graph.invoke(state, thread_config)
    
    if len(result["messages"]) > config.max_conversation_history:
        result["messages"] = result["messages"][-config.max_conversation_history:]
    
    for m in result["messages"]:
        m.pretty_print()
    
    return result