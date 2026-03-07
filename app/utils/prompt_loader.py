import re
from pathlib import Path
from typing import Optional, List
from app.utils.logger import logger
from app.utils.file_loader import load_file_from_path

# Path to the prompts directory relative to this file
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def get_prompt(prompt_name: str, version: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a prompt from the prompts directory.
    Format: <PROMPT_NAME>_<VERSION>.md
    If version is not provided, the latest version is returned.
    """
    try:
        if not PROMPTS_DIR.exists():
            logger.error("Prompts directory not found", path=str(PROMPTS_DIR))
            return None

        # Pattern to match prompt files: <name>_v<version>.md
        # We assume version starts with 'v' based on clinical_note_extraction_v1.md
        pattern = re.compile(rf"^{re.escape(prompt_name)}_(v?\d+)\.md$")
        
        available_files = []
        for f in PROMPTS_DIR.glob(f"{prompt_name}_*.md"):
            match = pattern.match(f.name)
            if match:
                v_str = match.group(1)
                # Extract numeric part for comparison if it's like 'v1'
                v_num = int(re.sub(r"\D", "", v_str))
                available_files.append((v_num, f))

        if not available_files:
            logger.warning("No prompt versions found", prompt_name=prompt_name)
            return None

        # Sort by version number
        available_files.sort(key=lambda x: x[0])

        target_file = None

        if version:
            # Look for specific version
            requested_v = int(re.sub(r"\D", "", version))
            for v_num, f in available_files:
                if v_num == requested_v:
                    target_file = f
                    break
            
            if not target_file:
                logger.warning("Specific prompt version not found", prompt_name=prompt_name, requested_version=version)
                return None
        else:
            # Get the latest
            latest_v, target_file = available_files[-1]
            logger.info("Using latest prompt version", prompt_name=prompt_name, version=latest_v)

        logger.info("Loading prompt", prompt_name=prompt_name, file=target_file.name)
        return load_file_from_path(target_file)

    except Exception as e:
        logger.error("Error retrieving prompt", prompt_name=prompt_name, error=str(e), exc_info=True)
        return None
