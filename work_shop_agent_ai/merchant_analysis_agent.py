"""
LangGraph Agent for Merchant Transaction Analysis.

This agent uses BigQuery tools to:
1. Get merchant statistics from BigQuery
2. Identify merchants with q50/avg ratio > 1.5
3. Analyze their transactions to understand patterns
4. Provide insights on anomalous transaction behavior
"""

import json
import os
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.schema import AgentAction, AgentFinish

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from bigquery_tools import BIGQUERY_TOOLS, get_merchant_statistics, get_merchant_transactions, analyze_merchant_anomalies


class AgentState(TypedDict):
    """State definition for the merchant analysis agent."""
    messages: Annotated[List[Any], "Messages in the conversation"]
    current_step: str
    merchant_data: Dict[str, Any]
    high_ratio_merchants: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    current_merchant_id: str
    iteration_count: int


class MerchantAnalysisAgent:
    """LangGraph-based agent for merchant transaction analysis."""
    
    def __init__(self, openai_api_key: str = None, model_name: str = "gpt-4o-mini"):
        """Initialize the merchant analysis agent."""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(
            api_key=self.openai_api_key,
            model=model_name,
            temperature=0.1
        )
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(BIGQUERY_TOOLS)
        
        # Create tool node
        self.tool_node = ToolNode(BIGQUERY_TOOLS)
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        # Add memory
        memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=memory)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for merchant analysis."""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("start_analysis", self._start_analysis)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("process_merchant_data", self._process_merchant_data)
        workflow.add_node("analyze_merchant", self._analyze_merchant)
        workflow.add_node("compile_results", self._compile_results)
        
        # Add edges
        workflow.set_entry_point("start_analysis")
        
        workflow.add_edge("start_analysis", "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "process_merchant_data": "process_merchant_data",
                "analyze_merchant": "analyze_merchant", 
                "compile_results": "compile_results",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("process_merchant_data", "agent")
        workflow.add_edge("analyze_merchant", "agent")
        workflow.add_edge("compile_results", END)
        
        return workflow
    
    def _start_analysis(self, state: AgentState) -> AgentState:
        """Initialize the analysis workflow."""
        system_message = SystemMessage(content="""
        You are a specialized merchant transaction analysis agent. Your job is to:
        
        1. Get merchant statistics from BigQuery using get_merchant_statistics tool
        2. Identify merchants with q50/avg ratio > 1.5
        3. For each high-ratio merchant, get their detailed transactions using get_merchant_transactions
        4. Analyze transaction patterns to understand what causes the high ratio using analyze_merchant_anomalies
        5. Provide comprehensive insights and recommendations
        
        Start by getting the merchant statistics data. Focus on finding actionable insights about merchant behavior patterns.
        """)
        
        state["messages"] = [system_message]
        state["current_step"] = "get_merchant_stats"
        state["merchant_data"] = {}
        state["high_ratio_merchants"] = []
        state["analysis_results"] = []
        state["current_merchant_id"] = ""
        state["iteration_count"] = 0
        
        return state
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Main agent decision-making node."""
        messages = state["messages"]
        
        # Add current step context to help the agent decide what to do next
        step_prompts = {
            "get_merchant_stats": "Start by calling get_merchant_statistics to get the list of merchants with their q50, avg amounts, and transaction counts.",
            "process_merchants": "Now identify merchants with q50/avg ratio > 1.5 from the data you just received.",
            "analyze_transactions": f"Get detailed transactions for merchant {state['current_merchant_id']} using get_merchant_transactions.",
            "analyze_patterns": f"Analyze the transaction patterns for merchant {state['current_merchant_id']} using analyze_merchant_anomalies.",
            "compile_final": "Compile your final analysis results with insights about merchants with high q50/avg ratios."
        }
        
        if state["current_step"] in step_prompts:
            step_message = HumanMessage(content=step_prompts[state["current_step"]])
            messages = messages + [step_message]
        
        response = self.llm_with_tools.invoke(messages)
        
        # Update messages
        state["messages"] = messages + [response]
        state["iteration_count"] += 1
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine the next step in the workflow."""
        last_message = state["messages"][-1]
        
        # If the agent used tools, go to tools node
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Route based on current step and content
        current_step = state["current_step"]
        
        if current_step == "get_merchant_stats":
            return "process_merchant_data"
        elif current_step == "process_merchants" and state["high_ratio_merchants"]:
            return "analyze_merchant"
        elif current_step == "analyze_transactions":
            return "analyze_merchant" 
        elif current_step == "analyze_patterns":
            # Check if we have more merchants to analyze
            analyzed_count = len(state["analysis_results"])
            total_high_ratio = len(state["high_ratio_merchants"])
            if analyzed_count < total_high_ratio and analyzed_count < 5:  # Limit to 5 merchants
                return "analyze_merchant"
            else:
                return "compile_results"
        elif current_step == "compile_final":
            return "end"
        
        return "end"
    
    def _process_merchant_data(self, state: AgentState) -> AgentState:
        """Process merchant data to identify high-ratio merchants."""
        messages = state["messages"]
        
        # Look for merchant statistics in recent tool responses
        for message in reversed(messages):
            if hasattr(message, 'content') and 'merchants' in str(message.content):
                try:
                    # Extract JSON data from the tool response
                    content = str(message.content)
                    if '{' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_str = content[json_start:json_end]
                        merchant_data = json.loads(json_str)
                        
                        # Filter for merchants with q50/avg ratio > 1.5
                        high_ratio_merchants = []
                        if 'merchants' in merchant_data:
                            for merchant in merchant_data['merchants']:
                                ratio = merchant.get('q50_avg_ratio', 0)
                                if ratio > 1.5:
                                    high_ratio_merchants.append(merchant)
                        
                        state["merchant_data"] = merchant_data
                        state["high_ratio_merchants"] = high_ratio_merchants
                        state["current_step"] = "process_merchants"
                        
                        # Add summary message
                        summary_msg = AIMessage(content=f"""
                        Found {len(high_ratio_merchants)} merchants with q50/avg ratio > 1.5:
                        {json.dumps(high_ratio_merchants[:3], indent=2)}
                        
                        Will now analyze transactions for each of these merchants.
                        """)
                        state["messages"].append(summary_msg)
                        break
                        
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return state
    
    def _analyze_merchant(self, state: AgentState) -> AgentState:
        """Analyze a specific merchant's transactions."""
        high_ratio_merchants = state["high_ratio_merchants"]
        analyzed_count = len(state["analysis_results"])
        
        if analyzed_count < len(high_ratio_merchants) and analyzed_count < 5:
            # Get the next merchant to analyze
            merchant = high_ratio_merchants[analyzed_count]
            merchant_id = merchant["merchant_id"]
            state["current_merchant_id"] = merchant_id
            state["current_step"] = "analyze_transactions"
            
            # Add message to get transactions for this merchant
            analysis_msg = HumanMessage(content=f"""
            Now analyze merchant {merchant_id} (q50/avg ratio: {merchant.get('q50_avg_ratio', 'N/A')}).
            First get their detailed transactions, then analyze the patterns.
            """)
            state["messages"].append(analysis_msg)
        else:
            state["current_step"] = "compile_final"
        
        return state
    
    def _compile_results(self, state: AgentState) -> AgentState:
        """Compile final analysis results."""
        high_ratio_merchants = state["high_ratio_merchants"]
        analysis_results = state["analysis_results"]
        
        # Create comprehensive summary
        summary = {
            "analysis_summary": {
                "total_merchants_analyzed": len(state["merchant_data"].get("merchants", [])),
                "high_ratio_merchants_found": len(high_ratio_merchants),
                "detailed_analysis_completed": len(analysis_results),
                "analysis_timestamp": datetime.now().isoformat()
            },
            "high_ratio_merchants": high_ratio_merchants,
            "detailed_analysis": analysis_results,
            "insights": {
                "common_patterns": "Analysis of transaction patterns in merchants with q50/avg > 1.5",
                "recommendations": "Recommendations for monitoring and action"
            }
        }
        
        final_message = AIMessage(content=f"""
        ## Merchant Analysis Complete
        
        **Summary:**
        - Analyzed {len(state["merchant_data"].get("merchants", []))} total merchants
        - Found {len(high_ratio_merchants)} merchants with q50/avg ratio > 1.5
        - Completed detailed analysis for {len(analysis_results)} merchants
        
        **High-Ratio Merchants:**
        {json.dumps(high_ratio_merchants, indent=2)}
        
        **Key Insights:**
        - Merchants with high q50/avg ratios often show bimodal transaction distributions
        - Large outlier transactions can significantly impact the ratio
        - Patterns suggest potential changes in business models or customer behavior
        
        **Recommendations:**
        1. Monitor these merchants for unusual transaction patterns
        2. Investigate large transaction outliers 
        3. Set up alerts for significant ratio changes
        4. Consider business verification for merchants with extreme ratios
        """)
        
        state["messages"].append(final_message)
        state["current_step"] = "completed"
        
        return state
    
    def run_analysis(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the complete merchant analysis workflow."""
        if config is None:
            config = {"configurable": {"thread_id": f"merchant_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}
        
        # Initialize with empty state
        initial_state = {
            "messages": [],
            "current_step": "start",
            "merchant_data": {},
            "high_ratio_merchants": [],
            "analysis_results": [],
            "current_merchant_id": "",
            "iteration_count": 0
        }
        
        # Run the workflow
        final_state = self.app.invoke(initial_state, config=config)
        
        return {
            "status": "completed",
            "high_ratio_merchants": final_state.get("high_ratio_merchants", []),
            "analysis_results": final_state.get("analysis_results", []),
            "messages": [msg.content if hasattr(msg, 'content') else str(msg) for msg in final_state.get("messages", [])],
            "total_iterations": final_state.get("iteration_count", 0)
        }


def create_merchant_analysis_agent(**kwargs) -> MerchantAnalysisAgent:
    """Factory function to create a merchant analysis agent."""
    return MerchantAnalysisAgent(**kwargs)
