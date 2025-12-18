"""Check if GraphRAG is being used vs LLM-only responses"""
import logging
from rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_graphrag():
    """Test and verify GraphRAG is working."""
    print("=" * 70)
    print("GraphRAG Verification Test")
    print("=" * 70)
    
    try:
        # Initialize RAG service
        print("\n[1/3] Initializing RAG Service...")
        rag = RAGService()
        print("✅ RAG Service initialized")
        
        # Test query
        test_query = "What is pneumonia?"
        print(f"\n[2/3] Testing query: '{test_query}'")
        print("-" * 70)
        
        # Process query
        result = rag.process_query(test_query)
        
        # Check GraphRAG info
        graphrag_info = result.get("graphrag_info", {})
        metadata = result.get("metadata", {})
        
        print("\n[3/3] GraphRAG Analysis:")
        print("=" * 70)
        
        if graphrag_info:
            method = graphrag_info.get("method", "Unknown")
            print(f"\n✅ RETRIEVAL METHOD: {method}")
            
            if method == "GraphRAG":
                print("\n🎯 GraphRAG IS BEING USED!")
                print("-" * 70)
                print(f"   📊 Nodes Found: {graphrag_info.get('nodes_found', 0)}")
                print(f"   🔗 Graph Edges: {graphrag_info.get('edges_found', 0)}")
                print(f"   📈 Traversal Depth: {graphrag_info.get('graph_traversal_depth', 0)}")
                print(f"   🔍 Initial Matches: {graphrag_info.get('initial_matches', 0)}")
                print(f"   📝 Retrieval Method: {graphrag_info.get('retrieval_method', 'N/A')}")
                
                nodes_found = graphrag_info.get('nodes_found', 0)
                edges_found = graphrag_info.get('edges_found', 0)
                
                if nodes_found > 0:
                    print(f"\n✅ SUCCESS: Found {nodes_found} Q&A pairs from Milvus!")
                    if edges_found > 0:
                        print(f"✅ SUCCESS: Graph traversal found {edges_found} connections!")
                        print("\n💡 This means:")
                        print("   1. Vector search found similar Q&A pairs")
                        print("   2. Graph traversal found related medical concepts")
                        print("   3. LLM used this context to generate the answer")
                        print("\n✅ Response is from GraphRAG, not just LLM!")
                    else:
                        print("⚠️  WARNING: No graph edges found (depth=0 or no connections)")
                else:
                    print("❌ ERROR: No nodes found! GraphRAG may not be working correctly.")
            elif method == "Agentic RAG":
                print("\n🤖 Agentic RAG is being used")
                print(f"   Iterations: {graphrag_info.get('iterations', 0)}")
            else:
                print(f"\n⚠️  Unknown method: {method}")
        else:
            print("\n❌ ERROR: No GraphRAG info found!")
            print("   This might mean GraphRAG is not enabled or not working.")
        
        # Show sources
        sources = result.get("sources", [])
        print(f"\n📚 Sources Retrieved: {len(sources)}")
        if sources:
            print("\n   Sample sources:")
            for i, source in enumerate(sources[:3], 1):
                print(f"   [{i}] {source[:150]}...")
        
        # Show retrieval stats
        retrieval_stats = metadata.get("retrieval_stats", {})
        if retrieval_stats:
            print(f"\n📊 Retrieval Statistics:")
            print(f"   Sources count: {retrieval_stats.get('sources_count', 0)}")
            print(f"   Context length: {retrieval_stats.get('context_length', 0)} characters")
        
        # Final verdict
        print("\n" + "=" * 70)
        if graphrag_info and graphrag_info.get("method") == "GraphRAG" and graphrag_info.get("nodes_found", 0) > 0:
            print("✅ VERDICT: GraphRAG IS WORKING CORRECTLY!")
            print("   The response uses medical Q&A pairs from Milvus GraphRAG.")
        else:
            print("⚠️  VERDICT: GraphRAG may not be working correctly.")
            print("   Check configuration and Milvus connection.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_graphrag()
