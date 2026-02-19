import os
from typing import List, Dict, Any, Union

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def _get_gemini_model_name() -> str:
    """
    Returns the default Gemini chat model name.
    Override via GEMINI_MODEL_NAME if you want a different one.
    """
    # Use the model name that was confirmed working in your setup.
    # You can still override this via the GEMINI_MODEL_NAME environment variable.
    return os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")


def _get_gemini_embedding_model_name() -> str:
    """
    Returns the default Gemini embedding model name.
    Override via GEMINI_EMBEDDING_MODEL_NAME if you want a different one.
    """
    # Use the embedding model name that was confirmed working in your setup.
    return os.getenv("GEMINI_EMBEDDING_MODEL_NAME", "gemini-embedding-001")


def _ensure_configured():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
    genai.configure(api_key=api_key)


def get_gemini_chatbot_response(
    messages: List[Dict[str, Any]],
    model_name: str = None,
    temperature: float = 0.0,
) -> str:
    """
    Drop-in style helper similar to get_chatbot_response, but using Gemini.

    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    """
    _ensure_configured()
    if model_name is None:
        model_name = _get_gemini_model_name()

    model = genai.GenerativeModel(model_name)

    # Convert chat-style messages into a single prompt string
    parts: List[str] = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
        else:
            parts.append(str(content))

    prompt = "\n\n".join(parts)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            top_p=0.8,
            max_output_tokens=2000,
        ),
    )

    # Gemini responses expose .text for the primary text output
    return response.text or ""


def get_gemini_embedding(
    text_input: Union[str, List[str]],
    model_name: str = None,
):
    """
    Gemini embedding helper, analogous to get_embedding.
    Returns a list of embedding vectors.
    """
    _ensure_configured()
    if model_name is None:
        model_name = _get_gemini_embedding_model_name()

    # google-generativeai supports both single string and list of strings
    result = genai.embed_content(
        model=model_name,
        content=text_input,
        task_type="retrieval_document",
    )

    # The client returns a dict with "embedding" for single input,
    # or {"embedding": [...]} per item for batched input.
    if isinstance(text_input, list):
        # Batched
        return [item["embedding"] for item in result["embeddings"]]
    else:
        # Single
        return [result["embedding"]]


def double_check_json_output_gemini(
    json_string: str,
    model_name: str = None,
) -> str:
    """
    Gemini version of double_check_json_output:
    - Ask the model to validate/fix JSON and return only a valid JSON string.
    """
    _ensure_configured()
    if model_name is None:
        model_name = _get_gemini_model_name()

    prompt = f"""You will check this JSON string and correct any mistakes that will make it invalid.
Then you will return the corrected JSON string. Nothing else.

If the JSON is already correct just return it.

Do NOT return a single letter outside of the JSON string.
There is no need to explain anything – only return the JSON string.

JSON:
{json_string}
"""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text or ""



