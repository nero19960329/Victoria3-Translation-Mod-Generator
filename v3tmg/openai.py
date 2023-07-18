import openai
import os


def set_openai_configs() -> None:
    if os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.environ["OPENAI_API_KEY"]
    if os.getenv("OPENAI_PROXY"):
        openai.proxy = {
            "https": os.environ["OPENAI_PROXY"],
            "http": os.environ["OPENAI_PROXY"],
        }
