"""
State definitions for LangGraph project.

This module defines the state structures used throughout the graph execution.
"""

from typing import Dict, List, Optional, Any, TypedDict
from langchain_core.messages import BaseMessage


class GraphState(TypedDict):
    """
    Main state structure for the LangGraph workflow.
    
    This represents the state that flows through all nodes in the graph.
    Add or modify fields based on your specific use case.
    """
    
    # Messages and conversation history
    messages: List[BaseMessage]
    
    # User input and context
    user_input: str
    context: Optional[str]
    
    # Processing flags and metadata
    step_count: int
    current_node: str
    
    # Results and outputs
    result: Optional[str]
    confidence_score: Optional[float]
    
    # Additional metadata
    metadata: Dict[str, Any]
    
    # Error handling
    error: Optional[str]
    retry_count: int


class NodeConfig(TypedDict):
    """
    Configuration for individual nodes.
    """
    node_name: str
    max_retries: int
    timeout: Optional[int]
    parameters: Dict[str, Any]


class WorkflowState(TypedDict):
    """
    Extended state for complex workflows.
    
    Use this for more complex scenarios that require additional state tracking.
    """
    
    # Inherit from GraphState
    graph_state: GraphState
    
    # Workflow-specific state
    workflow_id: str
    stage: str
    completed_stages: List[str]
    
    # Decision tracking
    decisions: List[Dict[str, Any]]
    branch_taken: Optional[str]
    
    # Performance metrics
    start_time: Optional[float]
    end_time: Optional[float]
    execution_time: Optional[float]


# Helper functions for state management
def create_initial_state(user_input: str, context: Optional[str] = None) -> GraphState:
    """
    Create an initial state for the graph execution.
    
    Args:
        user_input: The initial user input
        context: Optional context information
        
    Returns:
        GraphState: Initial state object
    """
    return GraphState(
        messages=[],
        user_input=user_input,
        context=context,
        step_count=0,
        current_node="start",
        result=None,
        confidence_score=None,
        metadata={},
        error=None,
        retry_count=0
    )


def update_state(state: GraphState, **updates) -> GraphState:
    """
    Update the state with new values.
    
    Args:
        state: Current state
        **updates: Fields to update
        
    Returns:
        GraphState: Updated state
    """
    new_state = state.copy()
    new_state.update(updates)
    return new_state


def increment_step(state: GraphState, node_name: str) -> GraphState:
    """
    Increment the step count and update current node.
    
    Args:
        state: Current state
        node_name: Name of the current node
        
    Returns:
        GraphState: Updated state
    """
    return update_state(
        state,
        step_count=state["step_count"] + 1,
        current_node=node_name
    )
