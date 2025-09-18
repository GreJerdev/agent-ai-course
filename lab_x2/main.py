"""
Main entry point for the LangGraph project.

This file demonstrates how to set up and run a LangGraph workflow
using the defined state and nodes.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from state.state import GraphState, create_initial_state
from nodes.node import (
    start_node,
    processing_node,
    decision_node,
    finalization_node,
    error_handling_node,
    should_continue_processing,
    route_after_decision
)

# Load environment variables
load_dotenv()


def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow.
    
    Returns:
        StateGraph: Configured workflow graph
    """
    
    # Initialize the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes to the graph
    workflow.add_node("start", start_node)
    workflow.add_node("processing", processing_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("finalization_node", finalization_node)
    workflow.add_node("error_handling", error_handling_node)
    
    # Set entry point
    workflow.set_entry_point("start")
    
    # Add edges (connections between nodes)
    workflow.add_edge("start", "processing")
    workflow.add_edge("processing", "decision")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "processing": "processing",
            "finalization_node": "finalization_node",
            "error_handling": "error_handling"
        }
    )
    
    workflow.add_conditional_edges(
        "processing",
        should_continue_processing,
        {
            "processing": "processing",
            "finalization_node": "finalization_node",
            "error_handling": "error_handling"
        }
    )
    
    # Terminal edges
    workflow.add_edge("finalization_node", END)
    workflow.add_edge("error_handling", "processing")
    
    return workflow


def run_workflow(user_input: str, context: str = None) -> Dict[str, Any]:
    """
    Run the complete workflow with given input.
    
    Args:
        user_input: User's input message
        context: Optional context information
        
    Returns:
        Dict[str, Any]: Final state and results
    """
    
    print(f"🎯 Running workflow for: '{user_input}'")
    print("=" * 50)
    
    # Create initial state
    initial_state = create_initial_state(user_input, context)
    
    # Create and compile the workflow
    workflow = create_workflow()
    app = workflow.compile()
    
    try:
        # Run the workflow
        final_state = app.invoke(initial_state)
        
        print("=" * 50)
        print("🎉 Workflow completed successfully!")
        
        return {
            "success": True,
            "result": final_state.get("result"),
            "messages": final_state.get("messages", []),
            "metadata": final_state.get("metadata", {}),
            "final_state": final_state
        }
        
    except Exception as e:
        print(f"❌ Workflow failed with error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "final_state": None
        }


def interactive_mode():
    """
    Run the workflow in interactive mode.
    """
    
    print("🎮 Interactive Mode - Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        user_input = input("\n💬 Enter your message: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            print("⚠️ Please enter a valid message.")
            continue
            
        # Optional context input
        context = input("📝 Enter context (optional): ").strip()
        if not context:
            context = None
            
        # Run workflow
        result = run_workflow(user_input, context)
        
        # Display result
        if result["success"]:
            print(f"\n✅ Result: {result['result']}")
            metadata = result.get("metadata", {})
            if "execution_time" in metadata:
                print(f"⏱️ Execution time: {metadata['execution_time']:.2f}s")
        else:
            print(f"\n❌ Error: {result['error']}")


if __name__ == "__main__":
    workflow = create_workflow()
    app = workflow.compile()

    try:
        png = app.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png)
        interactive_mode()
    except Exception:
        # This requires some extra dependencies and is optional
        pass

    
        
    