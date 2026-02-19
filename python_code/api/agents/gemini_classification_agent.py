import json
from copy import deepcopy

from dotenv import load_dotenv

from .gemini_utils import get_gemini_chatbot_response, double_check_json_output_gemini

load_dotenv()


class GeminiClassificationAgent:
    """
    Gemini-based equivalent of ClassificationAgent.

    Output format is kept identical so it can plug into the same controller:
      {
        "role": "assistant",
        "content": "",
        "memory": {
          "agent": "classification_agent",
          "classification_decision": "<details_agent|order_taking_agent|recommendation_agent>"
        }
      }
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are a helpful AI assistant for a coffee shop application.
            Your task is to determine what agent should handle the user input. You have 3 agents to choose from:
            1. details_agent: Responsible for answering questions about the coffee shop, like location, delivery places, working hours, and details about menu items, or listing menu items.
            2. order_taking_agent: Responsible for taking orders from the user and managing the full order-taking conversation.
            3. recommendation_agent: Responsible for giving recommendations to the user about what to buy.

            VERY IMPORTANT ROUTING RULES:
            - If the user is ordering, adding/removing items, changing quantity, or talking about "my order",
              "add X", "remove X", "I want", "I'd like", "buy", "order", or quantities of products,
              you MUST choose "order_taking_agent".
            - Only choose "details_agent" when the user is just asking for information (menu, prices, timings, store info)
              without actually placing or changing an order.
            - Only choose "recommendation_agent" when the user clearly asks for suggestions like
              "What should I get?" or "Recommend me something", without specifying a concrete order.

            Your output MUST be a single, valid JSON object with this exact structure
            and nothing else before or after it (no markdown, no explanations):
            {
              "chain of thought": "<your reasoning>",
              "decision": "details_agent" or "order_taking_agent" or "recommendation_agent",
              "message": ""
            }
        """

        input_messages = [{"role": "system", "content": system_prompt}]
        input_messages += messages[-3:]

        raw_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )
        print("\n[GeminiClassificationAgent] Raw model output:")
        try:
            print(raw_output)
        except Exception:
            print("<unprintable output>")

        # We intentionally skip double_check_json_output_gemini here and
        # parse the raw_output ourselves so we can robustly handle cases
        # where Gemini wraps JSON in ```json ... ``` fences.
        return self.postprocess(raw_output)

    def postprocess(self, output: str):
        """
        Safely parse JSON from Gemini. If parsing fails for any reason,
        try to infer the decision from the text; otherwise default to details_agent
        so the flow continues.
        """
        try:
            if not output or not output.strip():
                raise ValueError("Empty JSON output from Gemini")
            cleaned = output.strip()

            # Strip ``` or ```json fences if present
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                # Drop first line with ``` or ```json
                if lines:
                    lines = lines[1:]
                # Drop trailing ``` line if present
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
            # Heuristic fallback: infer decision from the raw text
            text = output or ""
            decision = "details_agent"
            if "order_taking_agent" in text:
                decision = "order_taking_agent"
            elif "recommendation_agent" in text:
                decision = "recommendation_agent"

            data = {
                "decision": decision,
                "message": "",
            }

        print("[GeminiClassificationAgent] Parsed decision:", data.get("decision"))

        return {
            "role": "assistant",
            "content": data.get("message", ""),
            "memory": {
                "agent": "classification_agent",
                "classification_decision": data.get("decision", "details_agent"),
            },
        }



