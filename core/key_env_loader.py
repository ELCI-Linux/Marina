import os
from pathlib import Path

KEY_DIR = Path("~/Marina/.keys").expanduser()

# Maps key file prefixes to environment variables
KEY_ENV_MAP = {
    "gpt": "OPENAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "deepseek_r1": "DEEPSEEK_API_KEY",
    "openweather": "OPENWEATHER_API_KEY"
}

def load_env_keys(verbose=False):
    if not KEY_DIR.exists():
        KEY_DIR.mkdir(parents=True, exist_ok=True)
        return

    for file in KEY_DIR.glob("*_key"):
        prefix = file.stem.replace("_key", "").lower()
        env_var = KEY_ENV_MAP.get(prefix)
        if not env_var:
            if verbose:
                print(f"[KEY_ENV] No env mapping for: {file.name}")
            continue
        try:
            with open(file, "r") as f:
                value = f.read().strip()
                os.environ[env_var] = value
                if verbose:
                    print(f"[KEY_ENV] Set {env_var} from {file.name}")
        except Exception as e:
            if verbose:
                print(f"[KEY_ENV] Failed to read {file.name}: {e}")
