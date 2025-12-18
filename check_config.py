"""Check and display current RAG configuration"""
from config import (
    GRAPH_RAG_ENABLED, AGENTIC_RAG_ENABLED,
    GRAPH_MAX_DEPTH, RETRIEVAL_TOP_K
)

print("=" * 70)
print("RAG Configuration Check")
print("=" * 70)

print("\nCurrent Configuration:")
print("-" * 70)
print(f"  GraphRAG Enabled:     {GRAPH_RAG_ENABLED}")
print(f"  Agentic RAG Enabled:  {AGENTIC_RAG_ENABLED}")
print(f"  Graph Max Depth:      {GRAPH_MAX_DEPTH}")
print(f"  Retrieval Top K:      {RETRIEVAL_TOP_K}")

print("\nAnalysis:")
print("-" * 70)

if AGENTIC_RAG_ENABLED:
    print("  [WARNING] Agentic RAG is ENABLED")
    print("  [ERROR] GraphRAG will NOT be used")
    print("\n  To use GraphRAG:")
    print("     Add to .env file: AGENTIC_RAG_ENABLED=false")
else:
    print("  [OK] Agentic RAG is DISABLED")
    if GRAPH_RAG_ENABLED:
        print("  [OK] GraphRAG is ENABLED")
        print("  [OK] GraphRAG will be used!")
    else:
        print("  [WARNING] GraphRAG is DISABLED")
        print("  To enable GraphRAG:")
        print("     Add to .env file: GRAPH_RAG_ENABLED=true")

print("\n" + "=" * 70)
