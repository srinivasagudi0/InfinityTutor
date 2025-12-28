from openai import OpenAI
import json
import os
import logging
import sys
from typing import Any, Dict, Tuple, Optional
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Prefer package-relative imports; fallback for direct execution.
try:
    from . import prompts
    from ..config import key
except ImportError:  # e.g., when running the file directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(current_dir)
    project_root = os.path.dirname(package_root)
    for path in (project_root, package_root):
        if path and path not in sys.path:
            sys.path.insert(0, path)
    import importlib
    prompts = importlib.import_module("InfinityTutor.core.prompts")
    key = importlib.import_module("InfinityTutor.config.key")

load_dotenv()

client = OpenAI(api_key=key.OPENAI_API_KEY)

MEMORY_PATH = os.path.join(BASE_DIR, "memory", "state.json")
LOG_PATH = os.path.join(BASE_DIR, "memory", "logbook.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logger = logging.getLogger(__name__)
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("OpenAI client logger initialized; writing to %s", LOG_PATH)

def load_memory() -> Dict[str, Any]:
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Memory file invalid or unreadable; starting fresh.")
        return {}


def save_memory(memory: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    tmp_path = f"{MEMORY_PATH}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(memory, f, indent=2)
    os.replace(tmp_path, MEMORY_PATH)


def _parse_response_content(content: str, current_memory: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    if "---MEMORY---" not in content:
        # Preserve memory when model forgets to return the block.
        return content.strip(), current_memory
    visible, memory_block = content.split("---MEMORY---", 1)
    try:
        updated_memory = json.loads(memory_block.strip())
        return visible.strip(), updated_memory
    except json.JSONDecodeError:
        logger.warning("Failed to decode memory JSON from model response; keeping previous memory.")
        return visible.strip(), current_memory


def _extract_content(choice) -> Optional[str]:
    """Handle varied response shapes from OpenAI SDKs (string or parts)."""
    if not choice:
        return None
    message = getattr(choice, "message", None) or getattr(choice, "delta", None)
    if not message:
        return None
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Newer SDKs may return a list of parts; join text segments only.
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "".join(parts).strip() if parts else None
    return None


def process_command(command: str) -> str:
    # 1. Load persistent memory
    memory = load_memory()

    # 2. Build system prompt with memory
    system_prompt = prompts.SYSTEM_PROMPT.format(
        memory=json.dumps(memory, indent=2)
    )

    logger.info("Command received: %s", command)

    try:
        # 3. Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            temperature=0.7,
            max_tokens=1600
        )
    except Exception as exc:  # broad catch to surface issues to user without crashing loop
        logger.error("OpenAI request failed", exc_info=exc)
        return "Sorry, I had trouble reaching the model. Please try again."

    choice = response.choices[0] if response and getattr(response, "choices", None) else None
    content = _extract_content(choice)
    if not content:
        logger.error("Invalid response format from OpenAI: %s", response)
        return "Sorry, I received an invalid response. Please try again."

    visible_text, updated_memory = _parse_response_content(content, memory)
    if updated_memory is not memory:
        save_memory(updated_memory)
        logger.info("Memory updated with %d keys", len(updated_memory))

    logger.info("Response returned: %s", visible_text.replace("\n", " ")[:500])

    return visible_text
