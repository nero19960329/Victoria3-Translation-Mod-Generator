import json
from loguru import logger
import openai
from retry import retry
from typing import Dict, Any

import v3tmg.localization as localization


class Translator:
    """
    Performs translation of content using a translation model and localization mappings.
    """

    def __init__(self, model: str, localization_dict: Dict[str, str]):
        """
        Initializes the Translator instance.

        :param model: str, the translation model name.
        :param localization_dict: Dict[str, str], a dictionary containing language mappings.
        """

        self.model = model
        self.localization_dict = localization_dict

    def translate(self, content: str, target_language: str) -> Dict[str, Any]:
        """
        Translates the given content from English to the target language.

        :param content: str, the content to be translated.
        :param target_language: str, the target language code.
        :return: Dict[str, Any], the translated content.
        """

        translated_content = self._translate_string(content, target_language)
        return json.loads(translated_content)

    @retry(tries=3, delay=20)
    def _translate_string(self, english_text: str, target_language: str) -> str:
        """
        Translates the given English text to the target language using the specified model.

        This method internally calls the OpenAI's ChatGPT service for the translation.

        :param english_text: str, the English text to be translated.
        :param target_language: str, the target language code.
        :return: str, the translated text.
        """

        logger.debug(
            f"Translating {english_text} to {localization.get_language_name(self.localization_dict, target_language)} using {self.model}"
        )

        translation = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._build_system_message(target_language),
                },
                {
                    "role": "user",
                    "content": english_text,
                },
            ],
        )

        result = translation.choices[0]["message"]["content"]
        logger.debug(f"Translate result: {result}")
        return result

    def _build_system_message(self, target_language: str) -> str:
        """
        Builds the system message for translation.

        The system message is constructed based on the target language, providing instructions and requirements
        for the translation task.

        :param target_language: str, the target language code.
        :return: str, the system message for translation.
        """

        return f"""You are a historian from the Victorian era, a language expert and a geographer.
Could you please help me with the {localization.get_language_name(self.localization_dict, target_language)} localization of a mod for the game Victoria 3?
I will provide you with a JSON string.
Your task is to translate the JSON string into {localization.get_language_name(self.localization_dict, target_language)} JSON string.
Please note that some strings may contain formats such as `$xxx$` or `[xxx]`, which should not be translated.
You should only output the translated JSON string, and you should assure that the translated JSON string is valid.
Please assure that the translated string is composed by {localization.get_language_name(self.localization_dict, target_language)} characters.
Pay attention to the difference between similar languages like Simplified Chinese and Traditional Chinese and Japanese, make sure you are translating to the correct language."""
