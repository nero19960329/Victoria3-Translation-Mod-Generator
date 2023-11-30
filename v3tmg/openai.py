import os
import openai


def get_openai_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_API_BASE"],
    )
