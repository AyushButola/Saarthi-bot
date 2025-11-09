import json, os

CONFIG_PATH = "config.json"

def get_language():
    if not os.path.exists(CONFIG_PATH):
        return "english"
    with open(CONFIG_PATH, "r") as f:
        return json.load(f).get("language", "english")

def set_language(lang):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"language": lang}, f)
