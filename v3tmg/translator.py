import json
import os
from typing import Dict, Any

from loguru import logger
from retry import retry

import v3tmg.localization as localization
from v3tmg.openai import get_openai_client


class Translator:
    """
    Performs translation of content
    using a translation model and localization mappings.
    """

    def __init__(self, model: str, localization_dict: Dict[str, str]):
        """
        Initializes the Translator instance.
        Intializes the OpenAI API key and proxy if specified.

        :param model: str, the translation model name.
        :param localization_dict:
            Dict[str, str], a dictionary containing language mappings.
        """
        self.client = get_openai_client()

        self.model = model
        self.localization_dict = localization_dict

    def translate(self, content: str, target_language: str) -> Dict[str, Any]:
        """
        Translates the given content from English to the target language.

        :param content: str, the content to be translated.
        :param target_language: str, the target language code.
        :return: Dict[str, Any], the translated content.
        """

        return self._translate_string(content, target_language)

    @retry(tries=5, delay=20)
    def _translate_string(self, english_text: str, target_language: str) -> str:
        """
        Translates the given English text to
        the target language using the specified model.

        This method internally calls the
        OpenAI's ChatGPT service for the translation.

        :param english_text: str, the English text to be translated.
        :param target_language: str, the target language code.
        :return: str, the translated text.
        """

        target_language_name = localization.get_language_name(
            self.localization_dict,
            target_language,
        )
        logger.debug(
            f"Translating {english_text} to {target_language_name} using {self.model}"
        )

        try:
            translation = self.client.chat.completions.create(
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

            result = translation.choices[0].message.content

            assert json.loads(result), "Translation result is not valid JSON"
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise e

        logger.debug(f"Translate result: {result}")
        return result

    def _build_system_message(self, target_language: str) -> str:
        """
        Builds the system message to be used in the translation.

        :param target_language: str, the target language code.
        :return: str, the system message.
        """

        filepath = os.path.dirname(os.path.realpath(__file__))
        with open(
            os.path.join(filepath, "prompts", "translator.txt"),
            "r",
            encoding="utf-8",
        ) as f:
            prompt = f.read()
        return prompt.replace(
            "{dst_lang}",
            localization.get_language_name(
                self.localization_dict, target_language
            ),
        )
