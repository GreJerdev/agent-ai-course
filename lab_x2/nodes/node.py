"""
Node implementations for LangGraph project.

This module contains the core node functions that define the behavior
of each step in the graph workflow.
"""

import time
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from state.state import GraphState, increment_step, update_state


def start_node(state: GraphState) -> GraphState:
    """
    Entry point node for the graph.
    
    This node initializes the workflow and sets up the initial context.
    
    Args:
        state: Current graph state
        
    Returns:
        GraphState: Updated state
    """
    print(f"🚀 Starting workflow with input: {state['user_input']}")
    
    # Add system message to initialize conversation
    system_msg = SystemMessage(
        content="You are a helpful AI assistant processing user requests through a LangGraph workflow."
    )
    
    # Add user message
    user_msg = HumanMessage(content=state["user_input"])
    
    updated_state = increment_step(state, "start_node")
    updated_state["messages"] = [system_msg, user_msg]
    updated_state["metadata"]["start_time"] = time.time()
    
    print("✅ Start node completed")
    return updated_state


def processing_node(state: GraphState) -> GraphState:
    """
    Main processing node.
    
    This node performs the core logic of your application.
    Customize this based on your specific use case.
    
    Args:
        state: Current graph state
        
    Returns:
        GraphState: Updated state
    """
    print("🔄 Processing user request...")
    
    user_input = state["user_input"]
    context = state.get("context", "")
    
    # Simulate processing logic
    # Replace this with your actual processing logic
    processed_result = f"Processed: {user_input}"
    if context:
        processed_result += f" (with context: {context})"
    
    # Add processing message
    ai_msg = AIMessage(
        content=f"I'm processing your request: {user_input}"
    )
    
    updated_state = increment_step(state, "processing_node")
    updated_state["messages"].append(ai_msg)
    updated_state["result"] = processed_result
    updated_state["confidence_score"] = 0.85  # Example confidence score
    
    print(f"✅ Processing completed: {processed_result}")
    return updated_state


def decision_node(state: GraphState) -> GraphState:
    """
    Decision node that determines the next step in the workflow.
    
    This node can route the flow to different paths based on conditions.
    
    Args:
        state: Current graph state
        
    Returns:
        GraphState: Updated state with decision metadata
    """
    print("🤔 Making routing decision...")
    
    # Example decision logic
    confidence = state.get("confidence_score", 0.0)
    user_input = state["user_input"].lower()
    
    # Simple decision rules (customize based on your needs)
    if confidence > 0.8:
        decision = "high_confidence"
    elif "help" in user_input or "question" in user_input:
        decision = "needs_assistance"
    else:
        decision = "standard_processing"
    
    updated_state = increment_step(state, "decision_node")
    updated_state["metadata"]["decision"] = decision
    updated_state["metadata"]["decision_confidence"] = confidence
    
    print(f"✅ Decision made: {decision} (confidence: {confidence})")
    return updated_state


def finalization_node(state: GraphState) -> GraphState:
    """
    Final node that prepares the output and cleans up.
    
    Args:
        state: Current graph state
        
    Returns:
        GraphState: Final state
    """
    print("🏁 Finalizing workflow...")
    
    # Calculate execution time
    start_time = state["metadata"].get("start_time")
    end_time = time.time()
    execution_time = end_time - start_time if start_time else 0
    
    # Create final response
    final_result = state.get("result", "No result generated")
    final_msg = AIMessage(
        content=f"Final result: {final_result}\nExecution time: {execution_time:.2f}s"
    )
    
    updated_state = increment_step(state, "finalization_node")
    updated_state["messages"].append(final_msg)
    updated_state["metadata"]["end_time"] = end_time
    updated_state["metadata"]["execution_time"] = execution_time
    
    print(f"✅ Workflow completed in {execution_time:.2f}s")
    return updated_state


def error_handling_node(state: GraphState) -> GraphState:
    """
    Error handling node for managing failures and retries.
    
    Args:
        state: Current graph state
        
    Returns:
        GraphState: Updated state with error handling
    """
    print("⚠️ Handling error...")
    
    error_msg = state.get("error", "Unknown error occurred")
    retry_count = state.get("retry_count", 0)
    
    # Add error message
    error_ai_msg = AIMessage(
        content=f"An error occurred: {error_msg}. Retry count: {retry_count}"
    )
    
    updated_state = increment_step(state, "error_handling_node")
    updated_state["messages"].append(error_ai_msg)
    updated_state["retry_count"] = retry_count + 1
    
    # Clear error after handling
    updated_state["error"] = None
    
    print(f"✅ Error handled: {error_msg}")
    return updated_state


# Conditional functions for graph routing
def should_continue_processing(state: GraphState) -> str:
    """
    Determine if processing should continue or move to finalization.
    
    Args:
        state: Current graph state
        
    Returns:
        str: Next node name
    """
    confidence = state.get("confidence_score", 0.0)
    has_error = state.get("error") is not None
    
    if has_error:
        return "error_handling_node"
    elif confidence > 0.7:
        return "finalization_node"
    else:
        return "processing_node"


def route_after_decision(state: GraphState) -> str:
    """
    Route to different nodes based on decision outcome.
    
    Args:
        state: Current graph state
        
    Returns:
        str: Next node name
    """
    decision = state["metadata"].get("decision", "standard_processing")
    
    routing_map = {
        "high_confidence": "finalization_node",
        "needs_assistance": "processing_node",
        "standard_processing": "processing_node"
    }
    
    return routing_map.get(decision, "finalization_node")


# Node registry for easy access
NODE_REGISTRY = {
    "start_node": start_node,
    "processing_node": processing_node,
    "decision_node": decision_node,
    "finalization_node": finalization_node,
    "error_handling_node": error_handling_node,
}

# Conditional registry
CONDITIONAL_REGISTRY = {
    "should_continue_processing": should_continue_processing,
    "route_after_decision": route_after_decision,
}
