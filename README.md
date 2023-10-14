# Victoria3 Translation Mod Generator

## Description

Victoria3 Translation Mod Generator is a tool designed to automatically translate mods for the game Victoria 3 using OpenAI's translation capabilities. It supports translating from English to any language supported by the game.

## Usage

To use the mod generator, follow the instructions below:

### Prerequisites

Make sure you have the following installed:

- Python 3.8 or above
- Pip package manager

### Installation

Install the required dependencies:

```sh
cd victoria3-translation-mod-generator
pip install -r requirements.txt
```

### Running the Generator

The generator can be executed with the following command:

```sh
export OPENAI_API_KEY=<your_openai_api_key>
export OPENAI_PROXY=<your_openai_proxy> # Optional, e.g. "http://127.0.0.1:7890"
python -m v3tmg --src <path_to_source_dir> --dst <path_to_destination_dir> --language <target_language> --model <gpt_model_name>
```

The available command-line arguments are as follows:

- `--src`: Path to the source localization file of the mod in English (e.g., `D:\Steam\steamapps\workshop\content\529340\2962482328\localization\english`).
- `--dst`\: Path to the destination directory for the translated mod files (e.g., `C:\Users\myuser\Documents\Paradox Interactive\Victoria 3\mod\Industry Expanded Translation Mod`).
- `--language`: The target language for translation (e.g., `simp_chinese`). Only languages from the supported list can be chosen.
- `--model`: The name of the GPT model to use for translation. The default value is `gpt-3.5-turbo`.

## Supported Languages

The following languages are supported for translation:

- braz_por: Brazilian Portuguese
- english: English
- french: French
- german: German
- japanese: Japanese
- korean: Korean
- polish: Polish
- russian: Russian
- simp_chinese: Simplified Chinese
- spanish: Spanish
- turkish: Turkish
