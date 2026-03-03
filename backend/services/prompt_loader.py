"""
Prompt Loader — loads and renders interview prompt templates.

Reads prompt files from the `prompts/` directory and injects
interview configuration variables (position, difficulty, focus areas).
"""
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("services.prompt_loader")

# Resolve the prompts directory relative to the project root
_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(filename: str) -> str:
    """
    Read a prompt template file from the prompts/ directory.

    :param filename: Name of the file (e.g. "interviewer_system.txt").
    :returns: Raw template string.
    :raises FileNotFoundError: If the prompt file doesn't exist.
    """
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_interviewer_prompt(
    position: str = "Software Engineer",
    difficulty: str = "medium",
    focus_areas: Optional[list[str]] = None,
) -> str:
    """
    Build the full interviewer system prompt by loading the template
    and injecting interview configuration.

    :param position: Job position being interviewed for.
    :param difficulty: Interview difficulty level.
    :param focus_areas: List of topics to focus on.
    :returns: Rendered system prompt string.
    """
    template = load_prompt("interviewer_system.txt")

    areas_str = ", ".join(focus_areas) if focus_areas else "general skills"

    rendered = template.format(
        position=position,
        difficulty=difficulty,
        focus_areas=areas_str,
    )

    logger.debug(f"Built interviewer prompt: position={position}, difficulty={difficulty}")
    return rendered
