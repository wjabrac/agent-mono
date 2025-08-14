from __future__ import annotations

import os
import platform
from dotenv import load_dotenv

load_dotenv()


def str_to_bool(value):
    true_values = {"true", "yes", "1", "on", "t", "y"}
    false_values = {"false", "no", "0", "off", "f", "n"}
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    s = str(value).lower().strip()
    if s in true_values:
        return True
    if s in false_values:
        return False
    return True


def _arch_image() -> str:
    m = platform.machine().lower()
    if any(x in m for x in ("x86", "amd64", "i386")):
        return "tjbtech1/metachain:amd64_latest"
    return "tjbtech1/metachain:latest"


DOCKER_WORKPLACE_NAME = os.getenv("DOCKER_WORKPLACE_NAME", "workplace")
GITHUB_AI_TOKEN = os.getenv("GITHUB_AI_TOKEN")
AI_USER = os.getenv("AI_USER", "tjb-tech")
LOCAL_ROOT = os.getenv("LOCAL_ROOT", os.getcwd())

DEBUG = str_to_bool(os.getenv("DEBUG", False))
DEFAULT_LOG = str_to_bool(os.getenv("DEFAULT_LOG", False))
LOG_PATH = os.getenv("LOG_PATH")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
JSON_LOGS = str_to_bool(os.getenv("JSON_LOGS", False))
EVAL_MODE = str_to_bool(os.getenv("EVAL_MODE", False))
BASE_IMAGES = os.getenv("BASE_IMAGES") or _arch_image()

_OLLAMA_DEFAULT = "ollama/llama3.1:8b"
if os.getenv("COMPLETION_MODEL"):
    COMPLETION_MODEL = os.getenv("COMPLETION_MODEL")
elif os.getenv("OLLAMA_HOST"):
    COMPLETION_MODEL = _OLLAMA_DEFAULT
else:
    COMPLETION_MODEL = "claude-3-5-sonnet-20241022"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
MC_MODE = str_to_bool(os.getenv("MC_MODE", True))

FN_CALL = str_to_bool(os.getenv("FN_CALL", None))
API_BASE_URL = os.getenv("API_BASE_URL")
ADD_USER = str_to_bool(os.getenv("ADD_USER", None))

NOT_SUPPORT_SENDER = ["mistral", "groq"]
MUST_ADD_USER = ["deepseek-reasoner", "o1-mini", "deepseek-r1"]
NOT_SUPPORT_FN_CALL = ["o1-mini", "deepseek-reasoner", "deepseek-r1", "llama", "grok-2"]
NOT_USE_FN_CALL = ["deepseek-chat"] + NOT_SUPPORT_FN_CALL

if ADD_USER is None:
    ADD_USER = any(m in COMPLETION_MODEL for m in MUST_ADD_USER)

if FN_CALL is None:
    FN_CALL = not any(m in COMPLETION_MODEL for m in NOT_USE_FN_CALL)

NON_FN_CALL = any(m in COMPLETION_MODEL for m in NOT_SUPPORT_FN_CALL)

if EVAL_MODE:
    DEFAULT_LOG = False

