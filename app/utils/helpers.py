import json
import re

def extract_json_from_text(text: str) -> dict:
    """
    Extracts JSON from a string that might contain markdown blocks or extra text.
    Returns an empty dict if extraction fails.
    """
    try:
        # First try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # Try finding JSON block using regex
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding any object-like structure
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback safe response
    return {"reply": "I'm having trouble processing that right now.", "recommendations": [], "end_of_conversation": False}
