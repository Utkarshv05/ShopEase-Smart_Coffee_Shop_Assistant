from typing import Dict, Any

from agents import (
    AgentProtocol,
)
from agents.gemini_guard_agent import GeminiGuardAgent
from agents.gemini_classification_agent import GeminiClassificationAgent
from agents.gemini_details_agent import GeminiDetailsAgent
from agents.gemini_order_taking_agent import GeminiOrderTakingAgent
from agents.gemini_recommendation_agent import GeminiRecommendationAgent


class GeminiAgentController:
    """
    Local controller that wires all Gemini-based agents together.

    It keeps the same public interface as the RunPod AgentController:
      get_response(self, input: Dict[str, Any]) -> Dict[str, Any]
    where input = {"input": {"messages": [...]}}.
    """

    def __init__(self):
        self.guard_agent = GeminiGuardAgent()
        self.classification_agent = GeminiClassificationAgent()
        self.recommendation_agent = GeminiRecommendationAgent(
            "recommendation_objects/apriori_recommendations.json",
            "recommendation_objects/popularity_recommendation.csv",
        )

        self.agent_dict: Dict[str, AgentProtocol] = {
            "details_agent": GeminiDetailsAgent(),
            "order_taking_agent": GeminiOrderTakingAgent(self.recommendation_agent),
            "recommendation_agent": self.recommendation_agent,
        }

    def get_response(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # Extract user input
        job_input = input["input"]
        messages = job_input["messages"]

        # Guard
        guard_agent_response = self.guard_agent.get_response(messages)
        if guard_agent_response["memory"]["guard_decision"] == "not allowed":
            print("[GeminiAgentController] Guard decision: not allowed")
            return guard_agent_response
        print("[GeminiAgentController] Guard decision: allowed")

        # Classification
        classification_agent_response = self.classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"]["classification_decision"]
        print(f"[GeminiAgentController] Chosen agent: {chosen_agent}")

        # Delegate to chosen agent
        agent = self.agent_dict[chosen_agent]
        response = agent.get_response(messages)

        return response




