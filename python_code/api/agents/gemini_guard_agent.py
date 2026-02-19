import json
from copy import deepcopy

from dotenv import load_dotenv

from .gemini_utils import get_gemini_chatbot_response, double_check_json_output_gemini

load_dotenv()


class GeminiGuardAgent:
    """
    Gemini-based equivalent of GuardAgent.

    Interface:
        get_response(messages: List[Dict]) -> Dict with keys:
          - role
          - content
          - memory.guard_decision
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
            Your task is to determine whether the user is asking something relevant to the coffee shop or not.
            The user is allowed to:
            1. Ask questions about the coffee shop, like location, working hours, menu items and coffee shop related questions.
            2. Ask questions about menu items, they can ask for ingredients in an item and more details about the item.
            3. Make an order.
            4. Ask about recommendations of what to buy.

            The user is NOT allowed to:
            1. Ask questions about anything else other than our coffee shop.
            2. Ask questions about the staff or how to make a certain menu item.

            Your output MUST be valid JSON with this exact structure:
            {
              "chain of thought": "<your reasoning>",
              "decision": "allowed" or "not allowed",
              "message": "" if allowed, otherwise "Sorry, I can't help with that. Can I help you with your order?"
            }
        """

        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        # Call Gemini once; avoid the extra double-check call here to reduce
        # quota usage and the chance of hitting 429 rate limits.
        try:
            raw_output = get_gemini_chatbot_response(
                input_messages,
                model_name=self.model_name,
            )
        except Exception as e:
            # On any API error (including 429), default to "allowed"
            # so the rest of the pipeline can continue.
            print(f"[GeminiGuardAgent] Error calling Gemini: {e}")
            return {
                "role": "assistant",
                "content": "",
                "memory": {
                    "agent": "guard_agent",
                    "guard_decision": "allowed",
                },
            }

        return self.postprocess(raw_output)

    def postprocess(self, output: str):
        """
        Parse the JSON output from Gemini safely.
        If parsing fails or we get an empty string, default to "allowed"
        with an empty message so the rest of the pipeline can continue.
        """
        try:
            if not output or not output.strip():
                raise ValueError("Empty JSON output from Gemini")
            cleaned = output.strip()

            # Strip ``` or ```json fences if present
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines:
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            # Extract JSON object between first '{' and last '}'
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start : end + 1]

            data = json.loads(cleaned)
        except Exception:
            data = {
                "decision": "allowed",
                "message": "",
            }

        return {
            "role": "assistant",
            "content": data.get("message", ""),
            "memory": {
                "agent": "guard_agent",
                "guard_decision": data.get("decision", "allowed"),
            },
        }



