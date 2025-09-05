import os
import json

CONFIG_FILENAME = "app_config.json"


def get_config_path():
    # Gets absolute path to config in the project's root directory
    return os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)


def save_data(payload: dict):
    print(payload)
    path = get_config_path()
    try:
        with open(path, "w") as f:
            json.dump(payload, f, indent=4)
        print(f"✅ Config saved to {path}")
    except Exception as e:
        print(f"❌ Failed to save config: {e}")


def load_data() -> dict:
    path = get_config_path()

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ JSON file is corrupted. Returning empty config.")
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
    else:
        print("ℹ️ No config file found. Generating base config.")
        payload = {
            "server": "",
            "http_proxy": "",
            "https_proxy": "",
            "token": "",
            "username": "",
            "password": "",
            "auth_type": "Basic Auth",
            "proxy_option": "No",
            "theme": "Dark",
            "thread_count": "safe_mode",
        }
        save_data(payload)

    return {}  # Default fallback
