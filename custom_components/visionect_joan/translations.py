TRANSLATIONS = {
    "pl": {
        "state": "Status",
        "battery": "Bateria",
        # ... dodaj wszystkie klucze tłumaczeń ...
    },
    "en": {
        "state": "State",
        "battery": "Battery",
        # ... dodaj wszystkie klucze tłumaczeń ...
    }
}

def get_translation(lang, key):
    return TRANSLATIONS.get(lang, {}).get(key, key)