"""Test RAG Service with GraphRAG"""
import logging
from rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag():
    """Test RAG service with sample queries."""
    print("=" * 60)
    print("RAG Service Test")
    print("=" * 60)
    
    try:
        # Initialize RAG service
        print("\nInitializing RAG Service...")
        rag = RAGService()
        print("✅ RAG Service initialized")
        
        # Test queries
        test_queries = [
            "What is pneumonia?",
            "What are the symptoms of diabetes?",
            "How is hypertension treated?",
            "What causes chest pain?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print("\n" + "=" * 60)
            print(f"Test Query {i}/{len(test_queries)}")
            print("=" * 60)
            print(f"Query: {query}\n")
            
            try:
                # Process query
                result = rag.process_query(query)
                
                # Display response
                print("📋 Response:")
                print("-" * 60)
                response = result.get("response", "")
                if hasattr(response, 'content'):
                    print(response.content)
                else:
                    print(response)
                
                # Display sources
                sources = result.get("sources", [])
                if sources:
                    print(f"\n📚 Sources ({len(sources)}):")
                    print("-" * 60)
                    for j, source in enumerate(sources[:3], 1):
                        print(f"\n[{j}] {source[:300]}...")
                
                # Display GraphRAG info
                graphrag_info = result.get("graphrag_info", {})
                if graphrag_info:
                    print(f"\n📊 GraphRAG Information:")
                    print(f"   Method: {graphrag_info.get('method', 'N/A')}")
                    if graphrag_info.get('method') == 'GraphRAG':
                        print(f"   ✅ Nodes Found: {graphrag_info.get('nodes_found', 0)}")
                        print(f"   ✅ Graph Edges: {graphrag_info.get('edges_found', 0)}")
                        print(f"   ✅ Traversal Depth: {graphrag_info.get('graph_traversal_depth', 0)}")
                        print(f"   ✅ Retrieval Method: {graphrag_info.get('retrieval_method', 'N/A')}")
                        print(f"\n💡 This response came from GraphRAG (not just LLM)!")
                        print(f"   - Vector search found {graphrag_info.get('initial_matches', 0)} initial matches")
                        print(f"   - Graph traversal found {graphrag_info.get('nodes_found', 0)} total nodes")
                        print(f"   - {graphrag_info.get('edges_found', 0)} semantic connections were used")
                
                # Display metadata
                metadata = result.get("metadata", {})
                if metadata:
                    print(f"\n📋 Additional Metadata:")
                    print(f"   Input type: {metadata.get('input_type', 'N/A')}")
                    print(f"   Medical context: {metadata.get('medical_context', {}).get('has_medical_context', False)}")
                    retrieval_stats = metadata.get('retrieval_stats', {})
                    if retrieval_stats:
                        print(f"   Sources count: {retrieval_stats.get('sources_count', 0)}")
                        print(f"   Context length: {retrieval_stats.get('context_length', 0)} chars")
                
                print("\n✅ Query processed successfully!")
                
            except Exception as e:
                print(f"\n❌ Error processing query: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error initializing RAG Service: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag()
