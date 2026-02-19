from copy import deepcopy
import json
import os

from dotenv import load_dotenv
from pinecone import Pinecone

from .gemini_utils import get_gemini_chatbot_response, get_gemini_embedding

load_dotenv()


class GeminiDetailsAgent:
    """
    Gemini-based equivalent of DetailsAgent.
    Uses Gemini embeddings + Pinecone for retrieval, then Gemini for the final answer.
    """

    def __init__(self, model_name: str | None = None, embedding_model_name: str | None = None):
        self.model_name = model_name
        self.embedding_model_name = embedding_model_name
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME")

    def get_closest_results(self, index_name, input_embeddings, top_k: int = 2):
        index = self.pc.Index(index_name)
        results = index.query(
            namespace="ns1",
            vector=input_embeddings,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
        )
        return results

    def get_response(self, messages):
        messages = deepcopy(messages)

        user_message = messages[-1]["content"]

        # Try to use Gemini embeddings + Pinecone; if it fails (dimension mismatch, etc.),
        # fall back to answering using the local products.jsonl so we still stay
        # consistent with the actual app menu.
        source_knowledge = ""
        try:
            embedding = get_gemini_embedding(
                user_message,
                model_name=self.embedding_model_name,
            )[0]
            result = self.get_closest_results(self.index_name, embedding)
            source_knowledge = "\n".join(
                [x["metadata"]["text"].strip() + "\n" for x in result["matches"]]
            )
        except Exception as e:
            # Log to server console but don't break the user experience
            print(
                "GeminiDetailsAgent retrieval error with Pinecone; "
                f"falling back to local products.jsonl context: {e}"
            )
            try:
                source_knowledge = self._get_local_products_context()
            except Exception as inner_e:
                print(f"GeminiDetailsAgent local products fallback failed: {inner_e}")
                source_knowledge = ""

        prompt = f"""
        Using the contexts below, answer the query as a friendly waiter at ShopEase.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = """
        You are a customer support agent for a coffee shop called ShopEase in Mumbai.
        Answer every question as if you are a friendly waiter, providing clear information
        about menu items, ingredients, store details, and general help with their visit or order.
        """

        messages[-1]["content"] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )
        return self.postprocess(chatbot_output)

    def _get_local_products_context(self) -> str:
        """
        Fallback: build context directly from the same products.jsonl file
        that the Flask web_app uses. This keeps answers aligned with the
        actual menu shown in the app even if Pinecone is misconfigured.
        """
        # Current file: python_code/api/agents/gemini_details_agent.py
        # products.jsonl: python_code/products/products.jsonl
        current_dir = os.path.dirname(os.path.abspath(__file__))
        products_file = os.path.join(
            current_dir, "..", "..", "products", "products.jsonl"
        )

        lines = []
        try:
            with open(products_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        product = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    name = product.get("name", "")
                    category = product.get("category", "")
                    price = product.get("price", 0)
                    description = product.get("description", "")

                    snippet = f"Name: {name}\nCategory: {category}\nPrice: ₹{price}\nDescription: {description}\n"
                    lines.append(snippet)
        except FileNotFoundError:
            print(f"GeminiDetailsAgent could not find products file at {products_file}")
        except Exception as e:
            print(f"GeminiDetailsAgent error reading products file: {e}")

        return "\n".join(lines)

    def postprocess(self, output: str):
        return {
            "role": "assistant",
            "content": output,
            "memory": {
                "agent": "details_agent",
            },
        }



