import argparse
import codecs
import json
from loguru import logger
import openai
import os
from retry import retry
import yaml
from typing import Dict, Any

LOCALIZATION = {
    "braz_por": "Brazilian Portuguese",
    "english": "English",
    "french": "French",
    "german": "German",
    "japanese": "Japanese",
    "korean": "Korean",
    "polish": "Polish",
    "russian": "Russian",
    "simp_chinese": "Simplified Chinese",
    "spanish": "Spanish",
    "turkish": "Turkish",
}

DICT_SIZE_THRESHOLD = 2500


class Translator:
    def __init__(self, model: str):
        self.model = model

    def translate(self, content: str, target_language: str) -> Dict[str, Any]:
        translated_content = self._translate_string(content, target_language)
        return json.loads(translated_content)

    @retry(tries=3, delay=20)
    def _translate_string(self, english_text: str, target_language: str) -> str:
        logger.debug(
            f"Translating {english_text} to {LOCALIZATION[target_language]} using {self.model}"
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
        return f"""You are a historian from the Victorian era and a language expert.
Could you please help me with the {LOCALIZATION[target_language]} localization of a mod for the game Victoria 3?
I will provide you with a JSON string.
Your task is to translate the JSON string into {LOCALIZATION[target_language]} JSON string.
Please note that some strings may contain formats such as `$xxx$` or `[xxx]`, which should not be translated.
You should only output the translated JSON string, and you should assure that the translated JSON string is valid."""


def main(src: str, dst: str, language: str, translator: Translator) -> None:
    create_directories(dst, language)

    logger.info(
        f"Translating {src} to {dst} for {LOCALIZATION[language]} using {translator.model}"
    )

    for root, dirs, files in os.walk(src):
        for file in files:
            if file.endswith("_l_english.yaml") or file.endswith("_l_english.yml"):
                logger.info(f"Translating {file}")
                with codecs.open(
                    os.path.join(root, file), "r", encoding="utf-8-sig"
                ) as fin:
                    src_content = fin.read().replace(':0 "', ': "')
                    src_yaml = yaml.safe_load(src_content)
                    dst_yaml = translate_dict(src_yaml, language, translator)
                    with codecs.open(
                        os.path.join(
                            dst,
                            "localization",
                            language,
                            file.replace("english", language),
                        ),
                        "w",
                        encoding="utf-8-sig",
                    ) as fout:
                        yaml.dump(dst_yaml, fout, allow_unicode=True)


def create_directories(dst: str, language: str) -> None:
    os.makedirs(dst, exist_ok=True)
    os.makedirs(os.path.join(dst, "localization"), exist_ok=True)
    os.makedirs(os.path.join(dst, "localization", language), exist_ok=True)


def translate_dict(
    english_dict: Dict[str, Any], target_language: str, translator: Translator
) -> Dict[str, Any]:
    def dict_size(dict_obj: Dict[str, Any]) -> int:
        return sum([len(k) + len(v) for k, v in dict_obj.items()])

    target_dict_key = f"l_{target_language}"
    translated_dict = {target_dict_key: english_dict["l_english"]}
    buffer = {}

    for key, value in translated_dict[target_dict_key].items():
        if isinstance(value, str):
            buffer[key] = value
        if dict_size(buffer) >= DICT_SIZE_THRESHOLD:
            translate_and_update_buffer(
                buffer, translated_dict, target_dict_key, translator, target_language
            )
    if buffer:
        translate_and_update_buffer(
            buffer, translated_dict, target_dict_key, translator, target_language
        )

    for key, value in translated_dict[target_dict_key].items():
        translated_dict[target_dict_key][key] = f'0 "{value}"'
    return translated_dict


def translate_and_update_buffer(
    buffer: Dict[str, Any],
    translated_dict: Dict[str, Any],
    target_dict_key: str,
    translator: Translator,
    target_language: str,
) -> None:
    translated_buffer = translator.translate(json.dumps(buffer), target_language)
    translated_dict[target_dict_key].update(translated_buffer)
    buffer.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=str)
    parser.add_argument("--dst", type=str)
    parser.add_argument(
        "--language", type=str, default="simp_chinese", choices=LOCALIZATION.keys()
    )
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    args = parser.parse_args()

    translator = Translator(args.model)
    main(args.src, args.dst, args.language, translator)
