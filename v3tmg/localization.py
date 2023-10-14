from typing import Dict


def get_language_name(
    localization_dict: Dict[str, str],
    language: str,
) -> str:
    """
    Retrieves the name of the language based on the given language code.

    :param localization_dict: Dict[str, str], a dictionary containing language mappings.
    :param language: str, the language code.
    :return: str, the corresponding language name.
    """

    return localization_dict.get(language, "")
