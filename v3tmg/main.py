import argparse

from v3tmg.mod_translator import ModTranslator


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=str)
    parser.add_argument("--dst", type=str)
    parser.add_argument("--language", type=str, default="simp_chinese")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    args = parser.parse_args()

    localization_dict = {
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

    mod_translator = ModTranslator(
        args.model,
        localization_dict,
        dict_token_size_threshold=500,
    )
    mod_translator.translate_mod_files(args.src, args.dst, args.language)
