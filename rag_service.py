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
    AGENT_MAX_ITERATIONS, AGENT_REASONING_ENABLED, GRAPH_MAX_DEPTH,
    DEEPSEEK_MODEL_NAME, QWEN_ENABLED
)
from input_processing import InputProcessor
from agentic_orchestrator import AgenticOrchestrator
from context_integration import ContextIntegrator
from modelarts_client import ModelArtsClient

# LLM imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    logging.warning("LangChain imports not available. Some features may not work.")

# Use centralized logging config if available
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)


class RAGService:
    """
    Main RAG Service that coordinates all components according to the cloud architecture.
    """
    
    def __init__(self):
        """Initialize RAG Service with all components."""
        # Initialize components
        self.input_processor = InputProcessor()
        from config import MILVUS_API_KEY, MILVUS_USER, MILVUS_PASSWORD, MILVUS_USE_CLOUD
        # Initialize context integrator with Milvus Cloud
        self.context_integrator = ContextIntegrator(
            milvus_host=MILVUS_HOST,
            milvus_port=MILVUS_PORT,
            collection_name=MILVUS_COLLECTION_NAME,
            milvus_api_key=MILVUS_API_KEY,
            milvus_user=MILVUS_USER,
            milvus_password=MILVUS_PASSWORD,
            use_cloud=MILVUS_USE_CLOUD
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
        
        # Initialize LLM - Try ModelArts DeepSeek first, fallback to Gemini
        self.modelarts_client = ModelArtsClient()
        self.llm_gemini = None
        
        # Initialize Gemini as fallback
        try:
            from config import GOOGLE_API_KEY
            if GOOGLE_API_KEY:
                self.llm_gemini = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=LLM_TEMPERATURE,
                    google_api_key=GOOGLE_API_KEY
                )
                logger.info("✅ Gemini LLM initialized as fallback")
        except Exception as e:
            logger.warning(f"Gemini LLM not available: {str(e)}")
        
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
            graph_results = None
            
            if AGENTIC_RAG_ENABLED:
                logger.info("Step 3: Agentic Orchestration")
                plan = self.agentic_orchestrator.plan_task(
                    user_query,
                    processed_input
                )
                
                # Execute with reasoning
                # Use Gemini LLM for agentic orchestrator if available
                llm_for_agent = self.llm_gemini if self.llm_gemini else None
                if not llm_for_agent:
                    logger.warning("No LLM available for agentic orchestrator")
                execution_result = self.agentic_orchestrator.execute_with_reasoning(
                    plan,
                    self.context_integrator,
                    llm_for_agent
                )
                
                # Use orchestrated context
                integrated_context = execution_result.get("final_context", "")
            else:
                # Step 3: GraphRAG Retrieval (PRIMARY METHOD)
                logger.info("Step 3: GraphRAG Retrieval")
                graph_results = self.context_integrator.retrieve_graphrag_context(
                    query_embedding,
                    top_k=RETRIEVAL_TOP_K,
                    max_depth=GRAPH_MAX_DEPTH if GRAPH_RAG_ENABLED else 1
                )
                
                # Step 4: Context Integration
                logger.info("Step 4: Context Integration")
                integrated_context = self.context_integrator.integrate_contexts(
                    graph_results=graph_results
                )
                
                # Store for sources extraction
                vector_results = graph_results.get("qa_pairs", []) if graph_results else []
            
            # Step 6: Generate Response
            logger.info("Step 6: Generating Response")
            
            # Try DeepSeek/Qwen API first (direct or ModelArts), fallback to Gemini
            response_text = None
            llm_used = "unknown"
            
            # Check available models
            available_models = self.modelarts_client.get_available_models()
            logger.info(f"Available LLM models: {[m['name'] for m in available_models]}")
            
            # Check if Qwen should be used as primary (when QWEN_ENABLED=true)
            if QWEN_ENABLED and self.modelarts_client.is_qwen_available():
                logger.info(f"Using Qwen3-32B as primary model")
                full_prompt = self.prompt_template.format(
                    context=integrated_context,
                    question=user_query
                )
                api_response = self.modelarts_client.invoke_qwen(full_prompt)
                if api_response:
                    response_text = self.modelarts_client.extract_response_text(api_response)
                    llm_used = "qwen3-32b"
            
            # Check if DeepSeek should be used (supports multiple model names)
            if not response_text:
                deepseek_models = ["deepseek-chat", "deepseek-v3.1", "deepseek-v3"]
                use_deepseek = self.modelarts_client.is_available() and (
                    LLM_MODEL.lower() in deepseek_models or 
                    LLM_MODEL.lower().startswith("deepseek")
                )
                
                # Try DeepSeek API (direct or ModelArts) - includes Qwen fallback if configured
                if use_deepseek:
                    logger.info(f"Using DeepSeek API: {LLM_MODEL}")
                    full_prompt = self.prompt_template.format(
                        context=integrated_context,
                        question=user_query
                    )
                    api_response = self.modelarts_client.invoke_deepseek(full_prompt)
                    if api_response:
                        response_text = self.modelarts_client.extract_response_text(api_response)
                        llm_used = LLM_MODEL.lower()
            
            # Fallback to Gemini if ModelArts failed or not configured
            if not response_text and self.llm_gemini:
                logger.info("Falling back to Google Gemini")
                try:
                    from langchain_core.prompts import ChatPromptTemplate
                    prompt = ChatPromptTemplate.from_template(self.prompt_template)
                    chain = prompt | self.llm_gemini
                    response = chain.invoke({
                        "question": user_query,
                        "context": integrated_context
                    })
                    response_text = response.content if hasattr(response, 'content') else str(response)
                    llm_used = "gemini-2.5-flash"
                except Exception as e:
                    logger.error(f"Gemini fallback failed: {e}")
            
            # If still no response, return error
            if not response_text:
                return {
                    "response": "[Error] No LLM available. Please configure ModelArts or Gemini API key.",
                    "sources": [],
                    "context": integrated_context,
                    "metadata": processed_input
                }
            
            # Prepare sources and GraphRAG metadata
            sources = []
            graphrag_metadata = {}
            
            if not AGENTIC_RAG_ENABLED:
                # GraphRAG was used - extract detailed information
                graphrag_metadata = {
                    "method": "GraphRAG",
                    "enabled": GRAPH_RAG_ENABLED,
                    "max_depth": GRAPH_MAX_DEPTH if GRAPH_RAG_ENABLED else 1,
                    "nodes_found": len(graph_results.get("nodes", [])),
                    "edges_found": len(graph_results.get("edges", [])),
                    "initial_matches": len(graph_results.get("nodes", [])) if graph_results else 0,
                    "graph_traversal_depth": graph_results.get("depth", 0) if graph_results else 0,
                    "retrieval_method": "Vector Search + Graph Traversal"
                }
                
                # Use GraphRAG Q&A pairs as sources with similarity scores
                sources = []
                for idx, result in enumerate(vector_results[:5], 1):  # Top 5 Q&A pairs
                    similarity = result.get('similarity', 0.0)
                    question = result.get('question', '')
                    answer_text = result.get('response', '')
                    
                    source_text = f"[{idx}] Similarity: {similarity:.3f}\n"
                    source_text += f"Q: {question[:200]}...\n" if len(question) > 200 else f"Q: {question}\n"
                    source_text += f"A: {answer_text[:300]}..." if len(answer_text) > 300 else f"A: {answer_text}"
                    
                    sources.append(source_text)
            else:
                # Agentic RAG was used
                graphrag_metadata = {
                    "method": "Agentic RAG",
                    "enabled": AGENTIC_RAG_ENABLED,
                    "iterations": execution_result.get("iterations", 0) if execution_result else 0
                }
                
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
            
            # Add GraphRAG metadata to processed_input metadata
            enhanced_metadata = {
                **processed_input,
                "graphrag": graphrag_metadata,
                "retrieval_stats": {
                    "sources_count": len(sources),
                    "context_length": len(integrated_context)
                }
            }
            
            # Add LLM info to metadata
            enhanced_metadata["llm_used"] = llm_used
            
            return {
                "response": response_text,
                "sources": sources,
                "context": integrated_context[:1000] + "..." if len(integrated_context) > 1000 else integrated_context,
                "metadata": enhanced_metadata,
                "execution_trace": execution_result if AGENTIC_RAG_ENABLED else None,
                "graphrag_info": graphrag_metadata  # Explicit GraphRAG info
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            # Return user-friendly error message without exposing internal details
            error_message = "An error occurred while processing your query. Please try again."
            if logger.level <= logging.DEBUG:
                error_message += f" (Error: {str(e)})"
            
            return {
                "response": error_message,
                "sources": [],
                "context": "",
                "metadata": {"error": True},
                "execution_trace": None
            }

