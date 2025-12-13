import json
import re
from typing import Any, List, Union, Dict
from urllib.parse import urlparse, ParseResult
from pathlib import Path

def to_bool(value: str) -> bool:
    """Convert a string to a boolean."""
    if str(value).lower() in ("true", "1", "t", "yes", "y", "on"):
        return True
    if str(value).lower() in ("false", "0", "f", "no", "n", "off"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")

def to_list(value: str, delimiter: str = ",") -> List[str]:
    """Convert a comma-separated string to a list."""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]

def to_json(value: str) -> Any:
    """Parse a JSON string."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON value: {value}") from e

def to_url(value: str) -> ParseResult:
    """Parse a URL string."""
    if not value:
        raise ValueError("Empty URL")
    return urlparse(value)

def to_path(value: str) -> Path:
    """Convert a string to a Path object."""
    if not value:
        raise ValueError("Empty path")
    return Path(value)

def expand_vars(value: str, env: Dict[str, str]) -> str:
    """Expand ${VAR} placeholders in a string."""
    if not isinstance(value, str):
        return value
    
    pattern = re.compile(r'\$\{([^}]+)\}')
    
    def replace(match):
        key = match.group(1)
        return env.get(key, match.group(0)) # Return original if not found
        
    return pattern.sub(replace, value)

