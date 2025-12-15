"""
Agentic Orchestrator Module (Task Planner)
Coordinates the RAG pipeline with agentic reasoning and task planning.
Part of the Application Server (ECS) layer.
"""
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the orchestrator can handle."""
    SIMPLE_RETRIEVAL = "simple_retrieval"
    GRAPH_RAG = "graph_rag"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class AgenticOrchestrator:
    """
    Agentic RAG Orchestrator that plans and executes retrieval tasks
    with reasoning capabilities.
    """
    
    def __init__(self, max_iterations: int = 5, reasoning_enabled: bool = True):
        """
        Initialize the orchestrator.
        
        Args:
            max_iterations: Maximum number of reasoning iterations
            reasoning_enabled: Whether to enable agentic reasoning
        """
        self.max_iterations = max_iterations
        self.reasoning_enabled = reasoning_enabled
        self.iteration_history = []
    
    def plan_task(self, user_query: str, input_metadata: Dict) -> Dict[str, Any]:
        """
        Plan the retrieval and reasoning task based on user query.
        
        Args:
            user_query: User's query
            input_metadata: Metadata from input processing
            
        Returns:
            Task plan dictionary
        """
        # Determine task type
        task_type = self._determine_task_type(user_query, input_metadata)
        
        # Create execution plan
        plan = {
            "task_type": task_type,
            "query": user_query,
            "steps": self._create_execution_steps(task_type, user_query, input_metadata),
            "reasoning_required": self.reasoning_enabled and task_type != TaskType.SIMPLE_RETRIEVAL,
            "expected_iterations": self._estimate_iterations(task_type)
        }
        
        logger.info(f"Task planned: {task_type.value}")
        return plan
    
    def _determine_task_type(self, query: str, metadata: Dict) -> TaskType:
        """Determine the type of task based on query and metadata."""
        input_type = metadata.get("input_type", "general")
        
        # Check for comparative queries
        if any(word in query.lower() for word in ["compare", "difference", "versus", "vs", "better"]):
            return TaskType.COMPARATIVE_ANALYSIS
        
        # Check for multi-step reasoning
        if any(word in query.lower() for word in ["why", "how", "explain", "because", "reason"]):
            return TaskType.MULTI_STEP_REASONING
        
        # Check if graph context is needed
        if metadata.get("medical_context", {}).get("has_medical_context", False):
            return TaskType.GRAPH_RAG
        
        return TaskType.SIMPLE_RETRIEVAL
    
    def _create_execution_steps(self, task_type: TaskType, query: str, metadata: Dict) -> List[Dict]:
        """Create execution steps for the task."""
        steps = []
        
        if task_type == TaskType.SIMPLE_RETRIEVAL:
            steps = [
                {"step": 1, "action": "vector_retrieval", "description": "Retrieve relevant documents"},
                {"step": 2, "action": "context_integration", "description": "Integrate retrieved context"},
                {"step": 3, "action": "generate_response", "description": "Generate final response"}
            ]
        
        elif task_type == TaskType.GRAPH_RAG:
            steps = [
                {"step": 1, "action": "entity_extraction", "description": "Extract medical entities"},
                {"step": 2, "action": "vector_retrieval", "description": "Retrieve relevant documents"},
                {"step": 3, "action": "graph_traversal", "description": "Traverse knowledge graph"},
                {"step": 4, "action": "context_integration", "description": "Integrate vector and graph contexts"},
                {"step": 5, "action": "generate_response", "description": "Generate final response"}
            ]
        
        elif task_type == TaskType.MULTI_STEP_REASONING:
            steps = [
                {"step": 1, "action": "initial_retrieval", "description": "Initial document retrieval"},
                {"step": 2, "action": "reasoning", "description": "Agentic reasoning step"},
                {"step": 3, "action": "refined_retrieval", "description": "Refined retrieval based on reasoning"},
                {"step": 4, "action": "context_integration", "description": "Integrate all contexts"},
                {"step": 5, "action": "generate_response", "description": "Generate final response"}
            ]
        
        elif task_type == TaskType.COMPARATIVE_ANALYSIS:
            steps = [
                {"step": 1, "action": "extract_comparison_entities", "description": "Extract entities to compare"},
                {"step": 2, "action": "parallel_retrieval", "description": "Retrieve information for each entity"},
                {"step": 3, "action": "graph_traversal", "description": "Find relationships between entities"},
                {"step": 4, "action": "comparative_integration", "description": "Integrate comparative context"},
                {"step": 5, "action": "generate_response", "description": "Generate comparative response"}
            ]
        
        return steps
    
    def _estimate_iterations(self, task_type: TaskType) -> int:
        """Estimate number of iterations needed for the task."""
        estimates = {
            TaskType.SIMPLE_RETRIEVAL: 1,
            TaskType.GRAPH_RAG: 2,
            TaskType.MULTI_STEP_REASONING: 3,
            TaskType.COMPARATIVE_ANALYSIS: 2
        }
        return estimates.get(task_type, 1)
    
    def execute_with_reasoning(self, plan: Dict, context_integrator, llm) -> Dict[str, Any]:
        """
        Execute the plan with agentic reasoning.
        
        Args:
            plan: Task plan
            context_integrator: ContextIntegrator instance
            llm: LLM instance for reasoning
            
        Returns:
            Execution result with reasoning trace
        """
        self.iteration_history = []
        current_context = ""
        reasoning_trace = []
        
        for iteration in range(self.max_iterations):
            logger.info(f"Reasoning iteration {iteration + 1}/{self.max_iterations}")
            
            # Execute current step
            step_result = self._execute_step(
                plan["steps"][min(iteration, len(plan["steps"]) - 1)],
                plan["query"],
                current_context,
                context_integrator
            )
            
            # Update context
            current_context = step_result.get("context", current_context)
            
            # Agentic reasoning
            if plan["reasoning_required"] and iteration < self.max_iterations - 1:
                reasoning = self._agentic_reasoning(
                    plan["query"],
                    current_context,
                    step_result,
                    llm
                )
                reasoning_trace.append(reasoning)
                
                # Check if we should continue or stop
                if reasoning.get("should_stop", False):
                    logger.info("Agent decided to stop reasoning")
                    break
            
            self.iteration_history.append({
                "iteration": iteration + 1,
                "step": step_result,
                "context_length": len(current_context)
            })
        
        return {
            "final_context": current_context,
            "reasoning_trace": reasoning_trace,
            "iterations": len(self.iteration_history),
            "plan": plan
        }
    
    def _execute_step(self, step: Dict, query: str, current_context: str, context_integrator) -> Dict:
        """Execute a single step of the plan."""
        action = step.get("action", "")
        step_result = {
            "action": action,
            "description": step.get("description", ""),
            "context": current_context,
            "status": "completed"
        }
        
        # Execute action-specific logic
        if action == "vector_retrieval" and context_integrator:
            try:
                # Generate embedding for query (simplified - in production use proper embedding)
                # For now, just update context
                step_result["context"] = current_context + f"\n[Vector retrieval completed for: {query}]"
            except Exception as e:
                logger.error(f"Error in vector_retrieval step: {str(e)}")
                step_result["status"] = "error"
        
        elif action == "graph_traversal" and context_integrator:
            try:
                step_result["context"] = current_context + f"\n[Graph traversal completed]"
            except Exception as e:
                logger.error(f"Error in graph_traversal step: {str(e)}")
                step_result["status"] = "error"
        
        return step_result
    
    def _agentic_reasoning(self, query: str, context: str, step_result: Dict, llm) -> Dict:
        """
        Perform agentic reasoning to decide next steps.
        
        Args:
            query: Original user query
            context: Current accumulated context
            step_result: Result from current step
            llm: LLM for reasoning
            
        Returns:
            Reasoning result with decision
        """
        reasoning_prompt = f"""
        You are an AI agent planning a retrieval task. Analyze the current situation:
        
        Original Query: {query}
        Current Context Length: {len(context)} characters
        Last Step: {step_result.get('action', 'unknown')}
        
        Decide:
        1. Is the current context sufficient to answer the query?
        2. Should we continue retrieving more information?
        3. What specific information is still missing?
        
        Respond in JSON format:
        {{
            "sufficient": true/false,
            "should_stop": true/false,
            "missing_info": "description of missing information",
            "next_action": "suggested next action"
        }}
        """
        
        try:
            # Try to use LLM for reasoning if available
            if llm:
                try:
                    from langchain_core.prompts import ChatPromptTemplate
                    prompt = ChatPromptTemplate.from_template(reasoning_prompt)
                    chain = prompt | llm
                    response = chain.invoke({})
                    
                    # Parse LLM response (simplified - in production use proper JSON parsing)
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    # Try to extract JSON from response
                    import json
                    import re
                    json_match = re.search(r'\{[^}]+\}', content)
                    if json_match:
                        reasoning_result = json.loads(json_match.group())
                        return {
                            "sufficient": reasoning_result.get("sufficient", False),
                            "should_stop": reasoning_result.get("should_stop", False),
                            "missing_info": reasoning_result.get("missing_info", ""),
                            "next_action": reasoning_result.get("next_action", "continue"),
                            "llm_reasoning": content
                        }
                except Exception as llm_error:
                    logger.warning(f"LLM reasoning failed, using fallback: {str(llm_error)}")
            
            # Fallback: Simple heuristic-based decision
            return {
                "sufficient": len(context) > 500,
                "should_stop": len(context) > 1000,
                "missing_info": "Additional context may be needed" if len(context) < 1000 else "",
                "next_action": "continue_retrieval" if len(context) < 1000 else "stop"
            }
        except Exception as e:
            logger.error(f"Error in agentic reasoning: {str(e)}")
            return {
                "sufficient": True,
                "should_stop": True,
                "missing_info": "",
                "next_action": "stop"
            }

