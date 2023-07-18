import codecs
import json
from loguru import logger
import os
import re
from typing import Dict, Tuple, Any
import yaml

import v3tmg.localization as localization
from v3tmg.translator import Translator


def parse_content(content: str) -> Tuple[str, Dict[str, int]]:
    """
    Parses the given content string and extracts the indexes and src_content.

    The input string is expected to be in the following format:
        'l_english:\n x1:n1 "y1"\n x2: n2 "y2"\n x3: n3 "y3"\n...'

    Where:
        - l_english, x1, x2, x3, etc. are keys,
        - n1, n2, n3, etc. are optional index values for these keys,
        - y1, y2, y3, etc. are corresponding string values.

    The function returns two outputs:
        - src_content: a re-formatted string without index values and quotes around y-values.
        - indexes: a dictionary where the key is x1, x2, x3 and the value is n1, n2, n3.

    :param content: str, the input string to be parsed.
    :return: tuple (src_content, indexes).
    """

    header, rest = content.split(":", 1)
    pattern = re.compile(r'(\w+):\s*(\d+)?\s*"([^"]*)"', re.MULTILINE | re.DOTALL)
    matches = pattern.findall(rest)

    src_content = header + ":\n"
    indexes = {}

    for x, n, y in matches:
        y = y.replace("\n", " ").replace("\r", " ").strip()
        src_content += f" {x}: {y}\n"
        if n:
            indexes[x] = int(n)

    return src_content.strip(), indexes


def create_directories(dst: str, language: str) -> None:
    """
    Creates the necessary directories for storing the translated mod files.

    :param dst: str, the destination directory.
    :param language: str, the target language code.
    """

    os.makedirs(dst, exist_ok=True)
    os.makedirs(os.path.join(dst, "localization"), exist_ok=True)
    os.makedirs(os.path.join(dst, "localization", language), exist_ok=True)


def dict_size(dict_obj: Dict[str, Any]) -> int:
    """
    Calculates the size of a dictionary by summing the lengths of its keys and values.

    :param dict_obj: Dict[str, Any], the dictionary object.
    :return: int, the size of the dictionary.
    """

    return sum([len(k) + len(v) for k, v in dict_obj.items()])


def update_yaml_with_indexes(yaml_dict: Dict[str, Any], indexes: Dict[str, int]):
    """
    Updates the translated YAML dictionary with the indexes.

    :param yaml_dict: Dict[str, Any], the translated YAML dictionary.
    :param indexes: Dict[str, int], the indexes dictionary.
    """

    yaml_key = list(yaml_dict.keys())[0]
    for k, v in yaml_dict[yaml_key].items():
        if k in indexes:
            yaml_dict[yaml_key][k] = f'{indexes[k]} "{v}"'
        else:
            yaml_dict[yaml_key][k] = f'"{v}"'


def build_yaml_content(yaml_dict: Dict[str, Any]) -> str:
    """
    Builds the YAML content from the translated dictionary.

    :param yaml_dict: Dict[str, Any], the translated YAML dictionary.
    :return: str, the YAML content.
    """

    yaml_key = list(yaml_dict.keys())[0]
    content = f"{yaml_key}:\n"
    for k, v in yaml_dict[yaml_key].items():
        content += f" {k}: {v}\n"
    return content.strip()


def is_mod_file(file: str) -> bool:
    """
    Checks if the given file is a mod file.

    :param file: str, the file name.
    :return: bool, True if the file is a mod file, False otherwise.
    """

    return file.endswith("_l_english.yaml") or file.endswith("_l_english.yml")


class ModTranslator:
    """
    Translates game mod files from English to the target language.
    """

    def __init__(
        self, model: str, localization_dict: Dict[str, str], dict_size_threshold: int
    ):
        """
        Initializes the ModTranslator instance.

        :param model: str, the translation model name.
        :param localization_dict: Dict[str, str], a dictionary containing language mappings.
        :param dict_size_threshold: int, the dictionary size threshold for translation.
        """

        self.translator = Translator(model, localization_dict)
        self.dict_size_threshold = dict_size_threshold

    def translate_mod_files(self, src: str, dst: str, language: str):
        """
        Translates the game mod files from English to the target language.

        :param src: str, the source directory containing the mod files.
        :param dst: str, the destination directory to store the translated mod files.
        :param language: str, the target language code.
        """

        create_directories(dst, language)

        logger.info(
            f"Translating {localization.get_language_name(self.translator.localization_dict, language)} using {self.translator.model}"
        )

        for root, dirs, files in os.walk(src):
            for file in files:
                if is_mod_file(file):
                    logger.info(f"Translating {file}")
                    self.translate_mod_file(os.path.join(root, file), dst, language)

    def translate_mod_file(self, file_path: str, dst: str, language: str):
        """
        Translates a single mod file from English to the target language.

        :param file_path: str, the path to the mod file.
        :param dst: str, the destination directory to store the translated mod files.
        :param language: str, the target language code.
        """

        with codecs.open(file_path, "r", encoding="utf-8-sig") as fin:
            content = fin.read()
            src_content, indexes = parse_content(content)
            src_yaml = yaml.safe_load(src_content)
            dst_yaml = self.translate_dict(src_yaml, language)
            update_yaml_with_indexes(dst_yaml, indexes)
            dst_content = build_yaml_content(dst_yaml)

        dst_filename = os.path.basename(file_path).replace("english", language)
        dst_filepath = os.path.join(dst, "localization", language, dst_filename)

        with codecs.open(dst_filepath, "w", encoding="utf-8-sig") as fout:
            fout.write(dst_content)

    def translate_dict(
        self, english_dict: Dict[str, Any], target_language: str
    ) -> Dict[str, Any]:
        """
        Translates the string values in the dictionary from English to the target language.

        :param english_dict: Dict[str, Any], the dictionary with English string values.
        :param target_language: str, the target language code.
        :return: Dict[str, Any], the translated dictionary.
        """

        target_dict_key = f"l_{target_language}"
        translated_dict = {target_dict_key: english_dict["l_english"]}
        buffer = {}

        for key, value in translated_dict[target_dict_key].items():
            if isinstance(value, str):
                buffer[key] = value
            if dict_size(buffer) >= self.dict_size_threshold:
                self.translate_and_update_buffer(
                    buffer, translated_dict, target_dict_key, target_language
                )
        if buffer:
            self.translate_and_update_buffer(
                buffer, translated_dict, target_dict_key, target_language
            )

        for key, value in translated_dict[target_dict_key].items():
            translated_dict[target_dict_key][key] = value
        return translated_dict

    def translate_and_update_buffer(
        self,
        buffer: Dict[str, Any],
        translated_dict: Dict[str, Any],
        target_dict_key: str,
        target_language: str,
    ) -> None:
        """
        Translates the strings in the buffer and updates the translated dictionary.

        :param buffer: Dict[str, Any], the buffer containing string values to be translated.
        :param translated_dict: Dict[str, Any], the translated dictionary.
        :param target_dict_key: str, the key for the target language in the translated dictionary.
        :param target_language: str, the target language code.
        """

        translated_buffer = self.translator.translate(
            json.dumps(buffer), target_language
        )
        dict_buffer = json.loads(translated_buffer)
        translated_dict[target_dict_key].update(dict_buffer)
        buffer.clear()
