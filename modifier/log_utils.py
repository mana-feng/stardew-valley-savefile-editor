import os
import tempfile

LOG_ENV_VAR = "SSE_LOG_DIR"
APP_NAME = "StardewSaveEditor"


def _default_log_dir():
    for key in ("LOCALAPPDATA", "APPDATA"):
        base = os.getenv(key)
        if base:
            return os.path.join(base, APP_NAME)
    return os.path.join(tempfile.gettempdir(), APP_NAME)


def get_log_dir():
    env_dir = os.getenv(LOG_ENV_VAR)
    if env_dir:
        return env_dir
    log_dir = _default_log_dir()
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        log_dir = tempfile.gettempdir()
    os.environ[LOG_ENV_VAR] = log_dir
    return log_dir


def get_log_path(filename):
    return os.path.join(get_log_dir(), filename)


def safe_write(path, text, mode="w"):
    try:
        with open(path, mode, encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception:
        return False


def safe_append(path, text):
    return safe_write(path, text, mode="a")
