import ast
import json
from copy import deepcopy

from dotenv import load_dotenv

from .gemini_utils import get_gemini_chatbot_response, double_check_json_output_gemini

load_dotenv()


class GeminiOrderTakingAgent:
    """
    Gemini-based equivalent of OrderTakingAgent.

    It keeps the same memory schema so it can be swapped with the original:
      memory: {
        "agent": "order_taking_agent",
        "step number": ...,
        "order": [...],
        "asked_recommendation_before": bool
      }
    """

    def __init__(self, recommendation_agent, model_name: str | None = None):
        self.model_name = model_name
        self.recommendation_agent = recommendation_agent

    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are a customer support Bot for a coffee shop called "ShopEase" in Mumbai.

            Here is the menu for this coffee shop (prices in INR):

            Cappuccino - ₹375
            Jumbo Savory Scone - ₹270
            Latte - ₹395
            Chocolate Chip Biscotti - ₹210
            Espresso shot - ₹165
            Hazelnut Biscotti - ₹230
            Chocolate Croissant - ₹310
            Dark chocolate (Drinking Chocolate) - ₹415
            Cranberry Scone - ₹290
            Croissant - ₹270
            Almond Croissant - ₹330
            Ginger Biscotti - ₹210
            Oatmeal Scone - ₹270
            Ginger Scone - ₹290
            Chocolate syrup - ₹125
            Hazelnut syrup - ₹125
            Carmel syrup - ₹125
            Sugar Free Vanilla syrup - ₹125
            Dark chocolate (Packaged Chocolate) - ₹250

            Things to NOT DO:
            * Don't ask how to pay by cash or card.
            * Don't tell the user to go to the counter.
            * Don't tell the user where to go to pick up the order.

            Your task is as follows:
            1. Take the user's order.
            2. Validate that all their items are in the menu.
            3. If an item is not in the menu, let the user know and repeat back the remaining valid order.
            4. Ask them if they need anything else.
            5. If they do, repeat from step 3.
            6. If they don't want anything else, then using the "order" object:
               a. List all items and their prices.
               b. Calculate the total.
               c. Thank the user for the order and close the conversation with no more questions.

            The user message may contain a "memory" section with:
              - "order"
              - "step number"
            Please utilize this information to determine the next step in the process.

            STRICT JSON AND ORDER RULES:
            - Your output MUST be a single, valid JSON object with this exact structure
              and nothing else before or after it (no markdown, no explanations):
              {
                "chain of thought": "<your reasoning>",
                "step number": "<current step number as a string>",
                "order": [ { "item": "<name>", "quantity": <int>, "price": <number> }, ... ],
                "response": "<what you say to the user>"
              }
            - When the user clearly asks to add, order, or change items (e.g. "I want 2 cappuccinos",
              "add one chocolate croissant", "remove 1 latte"), you MUST:
              * Reflect EVERY valid item and quantity in the "order" array.
              * Use the exact item names from the menu above (e.g. "Cappuccino", "Chocolate Croissant").
              * Set "quantity" to a positive integer.
              * Never return an empty "order" when the user has requested items.
            - Example:
              User: "I want 2 Cappuccinos and 1 Chocolate Croissant"
              Valid JSON (do not include this explanation in your output):
              {
                "chain of thought": "...",
                "step number": "2",
                "order": [
                  { "item": "Cappuccino", "quantity": 2, "price": 375 },
                  { "item": "Chocolate Croissant", "quantity": 1, "price": 310 }
                ],
                "response": "Great choice! I have added 2 Cappuccinos and 1 Chocolate Croissant to your order. Would you like anything else?"
              }
        """

        last_order_taking_status = ""
        asked_recommendation_before = False

        for message_index in range(len(messages) - 1, 0, -1):
            message = messages[message_index]

            agent_name = message.get("memory", {}).get("agent", "")
            if message["role"] == "assistant" and agent_name == "order_taking_agent":
                step_number = message["memory"]["step number"]
                order = message["memory"]["order"]
                asked_recommendation_before = message["memory"]["asked_recommendation_before"]
                last_order_taking_status = f"""
                step number: {step_number}
                order: {order}
                """
                break

        messages[-1]["content"] = last_order_taking_status + " \n " + messages[-1]["content"]

        input_messages = [{"role": "system", "content": system_prompt}] + messages

        raw_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )

        json_output = double_check_json_output_gemini(
            raw_output,
            model_name=self.model_name,
        )

        return self.postprocess(json_output, messages, asked_recommendation_before)

    def postprocess(self, output: str, messages, asked_recommendation_before: bool):
        """
        Safely parse JSON from Gemini. If parsing fails, fall back to an empty order and
        a generic response so the UI does not crash.
        """
        print("\n[GeminiOrderTakingAgent] Raw model output:")
        try:
            print(output)
        except Exception:
            # In case printing fails on some weird characters
            print("<unprintable output>")

        try:
            if not output or not output.strip():
                raise ValueError("Empty JSON output from Gemini")
            cleaned_output = self._extract_json_string(output)
            data = json.loads(cleaned_output)
        except Exception:
            data = {
                "step number": "1",
                "order": [],
                "response": "I'm here to help with your order. What would you like to have today?",
            }

        # Normalize order field to a list of objects with at least item + quantity
        if isinstance(data.get("order"), str):
            serialized_order = data["order"]
            parsed_order = []
            try:
                parsed_order = json.loads(serialized_order)
            except Exception:
                try:
                    parsed_order = ast.literal_eval(serialized_order)
                except Exception:
                    parsed_order = []
            data["order"] = parsed_order

        # Ensure order is a list
        if not isinstance(data.get("order"), list):
            data["order"] = []

        normalized_order = []
        for item in data["order"]:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except Exception:
                    try:
                        item = ast.literal_eval(item)
                    except Exception:
                        continue
            if not isinstance(item, dict):
                continue
            name = item.get("item") or item.get("name") or item.get("product") or ""
            qty = item.get("quantity") or item.get("qty") or 0
            try:
                qty = int(qty)
            except Exception:
                qty = 0
            if not name or qty <= 0:
                continue
            normalized_order.append(
                {
                    "item": name,
                    "quantity": qty,
                    "price": item.get("price", 0),
                }
            )

        data["order"] = normalized_order

        print("[GeminiOrderTakingAgent] Normalized order:")
        try:
            print(data["order"])
        except Exception:
            print("<unprintable order>")

        response = data.get("response", "")

        if not asked_recommendation_before and len(data.get("order", [])) > 0:
            recommendation_output = self.recommendation_agent.get_recommendations_from_order(
                messages,
                data["order"],
            )
            response = recommendation_output["content"]
            asked_recommendation_before = True

        return {
            "role": "assistant",
            "content": response,
            "memory": {
                "agent": "order_taking_agent",
                "step number": data.get("step number", "1"),
                "order": data.get("order", []),
                "asked_recommendation_before": asked_recommendation_before,
            },
        }

    def _extract_json_string(self, output: str) -> str:
        """
        Normalize Gemini output by stripping code fences or extra text so json.loads succeeds.
        """
        cleaned = output.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        return cleaned



