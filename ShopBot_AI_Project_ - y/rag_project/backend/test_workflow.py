#!/usr/bin/env python3
"""
Test LangGraph workflow
"""
from app.graph.workflow import support_graph

def test_workflow():
    # Test the graph with a simple query
    initial_state = {
        "session_id": "test123",
        "query": "What is your return policy?",
        "conversation_history": [],
        "intent": None,
        "retrieved_chunks": [],
        "confidence": 0.0,
        "answer": None,
        "is_escalated": False,
        "escalation_reason": None,
        "escalation_status": "none",
        "human_response": None,
        "error": None,
        "processing_start": 0
    }

    try:
        print("Testing workflow...")
        final_state = support_graph.invoke(initial_state)
        print("SUCCESS: Workflow completed")
        print(f"Answer: {final_state.get('answer', 'No answer')}")
    except Exception as e:
        print(f"ERROR: Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()