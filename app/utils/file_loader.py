from pathlib import Path
from typing import Optional
from app.utils.logger import logger

def load_file_from_path(file_path: str | Path) -> Optional[str]:
    """
    Loads the content of a file from the given path.
    Returns the string content if successful, or None if the file is not found.
    """
    path = Path(file_path)
    
    try:
        if not path.exists():
            logger.error("File not found", path=str(path))
            return None
            
        if not path.is_file():
            logger.error("Path is not a file", path=str(path))
            return None
            
        logger.info("Loading file", path=str(path))
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        logger.error("Failed to load file", path=str(path), error=str(e), exc_info=True)
        return None
