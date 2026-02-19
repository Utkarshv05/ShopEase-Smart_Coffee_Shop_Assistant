import json
import os
from copy import deepcopy

import pandas as pd
from dotenv import load_dotenv

from .gemini_utils import get_gemini_chatbot_response, double_check_json_output_gemini

load_dotenv()


class GeminiRecommendationAgent:
    """
    Gemini-based equivalent of RecommendationAgent.
    Keeps the same public methods:
      - recommendation_classification
      - get_response
      - get_recommendations_from_order
    and the same output structure used by the controller.
    """

    def __init__(self, apriori_recommendation_path, popular_recommendation_path, model_name: str | None = None):
        self.model_name = model_name

        with open(apriori_recommendation_path, "r") as file:
            self.apriori_recommendations = json.load(file)

        self.popular_recommendations = pd.read_csv(popular_recommendation_path)
        self.products = self.popular_recommendations["product"].tolist()
        self.product_categories = self.popular_recommendations["product_category"].tolist()

    def get_apriori_recommendation(self, products, top_k: int = 5):
        recommendation_list = []
        for product in products:
            if product in self.apriori_recommendations:
                recommendation_list += self.apriori_recommendations[product]

        recommendation_list = sorted(
            recommendation_list,
            key=lambda x: x["confidence"],
            reverse=True,
        )

        recommendations = []
        recommendations_per_category = {}
        for recommendation in recommendation_list:
            if recommendation in recommendations:
                continue

            product_category = recommendation["product_category"]
            if product_category not in recommendations_per_category:
                recommendations_per_category[product_category] = 0

            if recommendations_per_category[product_category] >= 2:
                continue

            recommendations_per_category[product_category] += 1
            recommendations.append(recommendation["product"])

            if len(recommendations) >= top_k:
                break

        return recommendations

    def get_popular_recommendation(self, product_categories=None, top_k: int = 5):
        recommendations_df = self.popular_recommendations

        if isinstance(product_categories, str):
            product_categories = [product_categories]

        if product_categories is not None:
            recommendations_df = self.popular_recommendations[
                self.popular_recommendations["product_category"].isin(product_categories)
            ]
        recommendations_df = recommendations_df.sort_values(
            by="number_of_transactions",
            ascending=False,
        )

        if recommendations_df.shape[0] == 0:
            return []

        recommendations = recommendations_df["product"].tolist()[:top_k]
        return recommendations

    def recommendation_classification(self, messages):
        system_prompt = f"""You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
We have 3 types of recommendations:

1. Apriori Recommendations: Based on items frequently bought together with the user's order.
2. Popular Recommendations: Based on overall popularity in the coffee shop.
3. Popular Recommendations by Category: User asks for a recommendation in a specific category (e.g., "What coffee do you recommend?").

Here is the list of items in the coffee shop:
{",".join(self.products)}

Here is the list of categories we have in the coffee shop:
{",".join(self.product_categories)}

Your task is to determine which type of recommendation to provide based on the user's message.

Your output MUST be a single, valid JSON object with this exact structure
and nothing else before or after it (no markdown, no explanations):
{{
  "chain of thought": "<your reasoning>",
  "recommendation_type": "apriori" or "popular" or "popular by category",
  "parameters": []  // a Python-style list: list of items (for apriori) or list of categories (for popular by category). Empty for popular.
}}
"""

        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]
        raw_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )
        json_output = double_check_json_output_gemini(
            raw_output,
            model_name=self.model_name,
        )
        return self.postprocess_classification(json_output)

    def get_response(self, messages):
        messages = deepcopy(messages)

        recommendation_classification = self.recommendation_classification(messages)
        recommendation_type = recommendation_classification["recommendation_type"]
        recommendations = []

        if recommendation_type == "apriori":
            recommendations = self.get_apriori_recommendation(recommendation_classification["parameters"])
        elif recommendation_type == "popular":
            recommendations = self.get_popular_recommendation()
        elif recommendation_type == "popular by category":
            recommendations = self.get_popular_recommendation(recommendation_classification["parameters"])

        if recommendations == []:
            return {
                "role": "assistant",
                "content": "Sorry, I can't help with that. Can I help you with your order?",
            }

        recommendations_str = ", ".join(recommendations)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        Your task is to recommend items to the user based on their input message.
        Respond in a friendly but concise way and present recommendations as a short unordered list with brief descriptions.
        """

        prompt = f"""
        {messages[-1]['content']}

        Please recommend these items exactly: {recommendations_str}
        """

        messages[-1]["content"] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )
        return self.postprocess(chatbot_output)

    def postprocess_classification(self, output: str):
        """
        Safely parse JSON from Gemini for recommendation classification.
        If parsing fails, default to popular recommendations with no parameters.
        """
        try:
            if not output or not output.strip():
                raise ValueError("Empty JSON output from Gemini")
            data = json.loads(output)
        except Exception:
            data = {
                "recommendation_type": "popular",
                "parameters": [],
            }

        return {
            "recommendation_type": data.get("recommendation_type", "popular"),
            "parameters": data.get("parameters", []),
        }

    def get_recommendations_from_order(self, messages, order):
        products = [product["item"] for product in order]
        recommendations = self.get_apriori_recommendation(products)
        recommendations_str = ", ".join(recommendations)

        system_prompt = """
        You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
        Your task is to recommend items to the user based on their current order.
        """

        prompt = f"""
        {messages[-1]['content']}

        Please recommend these items exactly: {recommendations_str}
        """

        messages[-1]["content"] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = get_gemini_chatbot_response(
            input_messages,
            model_name=self.model_name,
        )
        return self.postprocess(chatbot_output)

    def postprocess(self, output: str):
        return {
            "role": "assistant",
            "content": output,
            "memory": {
                "agent": "recommendation_agent",
            },
        }



