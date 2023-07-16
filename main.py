import argparse
import codecs
import json
from loguru import logger
import openai
import os
from retry import retry
import yaml

openai.api_key = os.environ["OPENAI_API_KEY"]
if os.getenv("OPENAI_PROXY"):
    openai.proxy = {
        "http": os.getenv("OPENAI_PROXY"),
        "https": os.getenv("OPENAI_PROXY"),
    }


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


def main(
    src: str,
    dst: str,
    language: str,
    translate_model: str = "gpt-3.5-turbo",
) -> None:
    # mkdir dst, dst/localization, dst/localization/{language}
    os.makedirs(dst, exist_ok=True)
    os.makedirs(os.path.join(dst, "localization"), exist_ok=True)
    os.makedirs(os.path.join(dst, "localization", language), exist_ok=True)

    logger.info(
        f"Translating {src} to {dst} for {LOCALIZATION[language]} using {translate_model}"
    )
    for root, dirs, files in os.walk(src):
        for file in files:
            logger.info(f"Translating {file}")
            if file.endswith("_l_english.yaml") or file.endswith("_l_english.yml"):
                with codecs.open(
                    os.path.join(root, file), "r", encoding="utf-8-sig"
                ) as fin:
                    src_content = fin.read()
                    src_content = src_content.replace(':0 "', ': "')
                    src_yaml = yaml.safe_load(src_content)
                    dst_yaml = translate_dict(src_yaml, language, translate_model)
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


def translate_dict(eng: dict, language: str, model: str) -> dict:
    def dict_size(d: dict) -> int:
        return sum([len(k) + len(v) for k, v in d.items()])

    DICT_SIZE_THRESHOLD = 2500

    sc = {f"l_{language}": eng["l_english"]}
    buffer = {}
    for k, v in sc[f"l_{language}"].items():
        if isinstance(v, str):
            buffer[k] = v
        if dict_size(buffer) >= DICT_SIZE_THRESHOLD:
            sc[f"l_{language}"].update(
                json.loads(translate_string(json.dumps(buffer), language, model))
            )
            buffer = {}
    if buffer:
        sc[f"l_{language}"].update(
            json.loads(translate_string(json.dumps(buffer), language, model))
        )
    for k, v in sc[f"l_{language}"].items():
        sc[f"l_{language}"][k] = f'0 "{v}"'
    return sc


@retry(tries=3, delay=20)
def translate_string(eng: str, language: str, model: str) -> str:
    logger.debug(f"Translating {eng} to {LOCALIZATION[language]} using {model}")

    s = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"""You are a historian from the Victorian era and a language expert.
Could you please help me with the {LOCALIZATION[language]} localization of a mod for the game Victoria 3?
I will provide you with a JSON string.
Your task is to translate the JSON string into {LOCALIZATION[language]} JSON string.
Please note that some strings may contain formats such as `$xxx$` or `[xxx]`, which should not be translated.
You should only output the translated JSON string, and you should assure that the translated JSON string is valid.""",
            },
            {
                "role": "user",
                "content": eng,
            },
        ],
    )
    d = s.choices[0]["message"]["content"]
    logger.debug(f"Translate result: {d}")
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=str)
    parser.add_argument("--dst", type=str)
    parser.add_argument(
        "--language", type=str, default="simp_chinese", choices=LOCALIZATION.keys()
    )
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    args = parser.parse_args()

    main(
        args.src,
        args.dst,
        args.language,
        args.model,
    )
