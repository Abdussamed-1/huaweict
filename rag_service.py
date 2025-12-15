"""
Main RAG Service that orchestrates all components.
This is the core service layer that coordinates Input Processing,
Agentic Orchestrator, Context Integration, and LLM.
"""
import logging
from typing import Dict, List, Optional, Any

from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME, LLM_MODEL, LLM_TEMPERATURE,
    RETRIEVAL_TOP_K, GRAPH_RAG_ENABLED, AGENTIC_RAG_ENABLED,
    AGENT_MAX_ITERATIONS, AGENT_REASONING_ENABLED
)
from input_processing import InputProcessor
from agentic_orchestrator import AgenticOrchestrator
from context_integration import ContextIntegrator

# LLM imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    logging.warning("LangChain imports not available. Some features may not work.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    """
    Main RAG Service that coordinates all components according to the cloud architecture.
    """
    
    def __init__(self):
        """Initialize RAG Service with all components."""
        # Initialize components
        self.input_processor = InputProcessor()
        self.context_integrator = ContextIntegrator(
            milvus_host=MILVUS_HOST,
            milvus_port=MILVUS_PORT,
            collection_name=MILVUS_COLLECTION_NAME
        )
        self.agentic_orchestrator = AgenticOrchestrator(
            max_iterations=AGENT_MAX_ITERATIONS,
            reasoning_enabled=AGENT_REASONING_ENABLED
        )
        
        # Initialize embedding model
        try:
            self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            self.embedding_model = None
        
        # Initialize LLM
        try:
            from config import GOOGLE_API_KEY
            self.llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                google_api_key=GOOGLE_API_KEY
            )
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            self.llm = None
        
        # Initialize prompt template
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> str:
        """Create the prompt template for medical responses."""
        return """
You are an experienced medical assistant supporting a doctor in evaluating a patient's symptoms. Based on the provided context and the doctor's question, respond clearly and professionally. Do not copy the context directly—paraphrase and interpret it to generate a medically sound, structured answer.

Your response **must** be divided into three clear paragraphs:
1. **Diagnosis**: State the most likely medical diagnosis using precise terminology.
2. **Clinical Reasoning**: Explain key findings from the context that support this diagnosis.
3. **Interpretation**: Provide guidance to help the doctor link the diagnosis to the patient's symptoms.

**Strict Content Guidelines**:
- If the input is unrelated to healthcare, diagnosis, or symptoms (e.g., general knowledge, greetings, names), reply:
  > "This system is designed exclusively for medical diagnostic assistance; I cannot answer unrelated questions."
- If the input lacks sufficient clinical detail (e.g., "I have a headache" without additional information), reply:
  > "More clinical information is required; please elaborate on symptoms and findings."

**Retrieval Check**:
- If there is no relevant medical context (e.g., retrieved documents list is empty or similarity scores are below threshold), reply:
  > "I'm sorry, I couldn't find enough relevant medical information to answer your question. Could you please provide more details about the patient's history and symptoms?"

Context:
{context}

Doctor's Question:
{question}

Respond only with the three paragraphs described. Do not add any extra sections or disclaimers.
"""
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            user_query: User's medical query
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Step 1: Input Processing
            logger.info("Step 1: Input Processing")
            processed_input = self.input_processor.preprocess(user_query)
            
            # Step 2: Generate query embedding
            logger.info("Step 2: Generating query embedding")
            if not self.embedding_model:
                return {
                    "response": "[Error] Embedding model not available.",
                    "sources": [],
                    "context": "",
                    "metadata": processed_input
                }
            
            query_embedding = self.embedding_model.embed_query(processed_input["processed_text"])
            
            # Step 3: Agentic Orchestration (if enabled)
            execution_result = None
            vector_results = []
            if AGENTIC_RAG_ENABLED:
                logger.info("Step 3: Agentic Orchestration")
                plan = self.agentic_orchestrator.plan_task(
                    user_query,
                    processed_input
                )
                
                # Execute with reasoning
                execution_result = self.agentic_orchestrator.execute_with_reasoning(
                    plan,
                    self.context_integrator,
                    self.llm
                )
                
                # Use orchestrated context
                integrated_context = execution_result["final_context"]
            else:
                # Step 3: Simple Vector Retrieval
                logger.info("Step 3: Vector Retrieval")
                vector_results = self.context_integrator.retrieve_vector_context(
                    query_embedding,
                    top_k=RETRIEVAL_TOP_K
                )
                
                # Step 4: GraphRAG (if enabled)
                graph_results = {"nodes": [], "edges": [], "context": ""}
                if GRAPH_RAG_ENABLED and processed_input.get("entities"):
                    logger.info("Step 4: GraphRAG Retrieval")
                    entity_ids = processed_input.get("entities", [])
                    graph_results = self.context_integrator.retrieve_graph_context(
                        entity_ids,
                        max_depth=3
                    )
                
                # Step 5: Context Integration
                logger.info("Step 5: Context Integration")
                integrated_context = self.context_integrator.integrate_contexts(
                    vector_results,
                    graph_results
                )
            
            # Step 6: Generate Response
            logger.info("Step 6: Generating Response")
            if not self.llm:
                return {
                    "response": "[Error] LLM not available.",
                    "sources": [],
                    "context": integrated_context,
                    "metadata": processed_input
                }
            
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_template(self.prompt_template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "question": user_query,
                "context": integrated_context
            })
            
            # Prepare sources
            sources = []
            if not AGENTIC_RAG_ENABLED:
                # Use already retrieved vector_results from above
                sources = [
                    result.get("text", "")[:500] + "..." 
                    if len(result.get("text", "")) > 500 
                    else result.get("text", "")
                    for result in vector_results
                ]
            else:
                # For agentic RAG, extract sources from execution trace if available
                if execution_result:
                    # Try to extract sources from iteration history
                    iteration_history = execution_result.get("plan", {}).get("steps", [])
                    if iteration_history:
                        sources = [
                            f"Step {step.get('step', '')}: {step.get('description', '')}"
                            for step in iteration_history
                        ]
                    else:
                        sources = ["Agentic reasoning completed"]
            
            return {
                "response": response.content if hasattr(response, 'content') else str(response),
                "sources": sources,
                "context": integrated_context[:1000] + "..." if len(integrated_context) > 1000 else integrated_context,
                "metadata": processed_input,
                "execution_trace": execution_result if AGENTIC_RAG_ENABLED else None
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": f"[GENERAL ERROR] {str(e)}",
                "sources": [],
                "context": "",
                "metadata": {},
                "execution_trace": None
            }

