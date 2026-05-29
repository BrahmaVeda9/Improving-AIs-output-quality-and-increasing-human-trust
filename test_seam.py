import sys
import os
from core.seam_db import save_message, get_chat_history, get_sessions, clear_session
from core.seam_llm import chat_completion, parse_signals_seam

def run_tests():
    print("=== STARTING SEAM AI INTEGRATION TESTS ===")
    
    # Test session ID
    test_session = "seam-test-session-999"
    
    # 1. Clear any existing test history
    print("\n--- Testing seam_db.py: clear_session ---")
    clear_session(test_session)
    history = get_chat_history(test_session)
    assert len(history) == 0, f"History should be empty, but got {len(history)}"
    print("Passed: clear_session successfully reset history.")
    
    # 2. Test saving messages with signals list
    print("\n--- Testing seam_db.py: save_message ---")
    mock_signals = [
        {
            "signal_type": "outdated",
            "exact_text": "2023 sales",
            "explanation": "Numbers change rapidly."
        }
    ]
    save_message(test_session, "user", "What are the sales numbers?")
    save_message(test_session, "assistant", "The 2023 sales were high.", mock_signals)
    
    history = get_chat_history(test_session)
    assert len(history) == 2, f"Expected 2 messages, got {len(history)}"
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert len(history[1]["signals"]) == 1, "Signals list should match"
    print("Passed: messages and signals saved/retrieved successfully.")
    
    # 3. Test get_sessions
    print("\n--- Testing seam_db.py: get_sessions ---")
    sessions = get_sessions()
    assert test_session in sessions, f"Session {test_session} not found in session list"
    print("Passed: get_sessions indexed active sessions.")
    
    # 4. Test parse_signals_seam (ON and OFF)
    print("\n--- Testing seam_llm.py: parse_signals_seam ---")
    raw_ai_text = "The 2023 sales were high."
    
    # Signals OFF
    parsed_off = parse_signals_seam(raw_ai_text, mock_signals, signals_on=False, message_index=1)
    assert parsed_off == "The 2023 sales were high.", f"Signals OFF mismatch: {parsed_off}"
    print("Passed: parse_signals_seam (OFF) successfully stripped tags.")
    
    # Signals ON
    parsed_on = parse_signals_seam(raw_ai_text, mock_signals, signals_on=True, message_index=1)
    assert "chip-container" in parsed_on, "Parsed HTML should contain chip container"
    assert "c-outdated" in parsed_on, "Parsed HTML should contain class c-outdated"
    assert "2023 sales" in parsed_on, "Parsed HTML should contain exact text"
    assert "Numbers change rapidly." in parsed_on, "Parsed HTML should contain explanation"
    print("Passed: parse_signals_seam (ON) successfully generated interactive CSS chips.")
    
    # 5. Test real Groq API JSON chat completion
    print("\n--- Testing seam_llm.py: chat_completion (Real API Call) ---")
    messages = [{"role": "user", "content": "What is the capital of France?"}]
    try:
        result = chat_completion(messages)
        print("Groq response payload keys:", list(result.keys()))
        assert "response" in result, "Result must contain 'response' key"
        assert "signals" in result, "Result must contain 'signals' key"
        print(f"Passed: Groq JSON response works. Result: {result}")
    except Exception as e:
        print(f"Error during Groq API call: {e}")
        print("If this fails due to network/keys, check environment settings.")
        sys.exit(1)
        
    # Clean up test session
    clear_session(test_session)
    print("\n=== ALL SEAM TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()
