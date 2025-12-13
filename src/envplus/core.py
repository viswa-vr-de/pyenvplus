import os
import sys
from typing import Any, List, Optional, Union, Dict
from pathlib import Path
from urllib.parse import ParseResult
from dotenv import dotenv_values
from .exceptions import MissingEnvError, ValidationError
from .utils import to_bool, to_list, to_json, to_url, to_path, expand_vars

class Env:
    def __init__(self, env_file: Union[str, List[str]] = ".env", strict: bool = False):
        if isinstance(env_file, str):
            self.env_files = [Path(env_file).resolve()]
        else:
            self.env_files = [Path(f).resolve() for f in env_file]
            
        self.strict = strict
        self._cache: Dict[str, str] = {}
        self._last_modified: Dict[Path, float] = {}
        self.load()

    def load(self) -> None:
        """Load environment variables from .env files and system environment."""
        new_cache = {}
        
        # Load from all files in order (later files override earlier ones)
        for file_path in self.env_files:
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                self._last_modified[file_path] = current_mtime
                # Load and merge
                file_values = dotenv_values(file_path)
                new_cache.update(file_values)
        
        self._cache = new_cache

    def _check_reload(self) -> None:
        """Check if any file has changed and reload if necessary."""
        should_reload = False
        for file_path in self.env_files:
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                if current_mtime > self._last_modified.get(file_path, 0):
                    should_reload = True
                    break
            elif file_path in self._last_modified:
                 # File was deleted
                 should_reload = True
                 break
        
        if should_reload:
            self.load()

    def _get_raw(self, key: str) -> Optional[str]:
        """Get raw string value from system env or .env file."""
        self._check_reload()

        # System env takes priority
        val = os.environ.get(key)
        if val is None:
            val = self._cache.get(key)
            
        if val is not None:
            # Expand variables using combined env (system + loaded)
            # We create a context for expansion that includes current process env and loaded values
            context = {**self._cache, **os.environ}
            return expand_vars(val, context)
            
        return None

    def get(self, key: str, default: Any = None, cast: Any = None) -> Any:
        """Get environment variable with optional casting."""
        value = self._get_raw(key)

        if value is None:
            if default is not None:
                return default
            if self.strict:
                raise MissingEnvError(f"Missing required environment variable: {key}")
            return None

        if cast:
            try:
                return cast(value)
            except Exception as e:
                raise ValidationError(f"Failed to cast {key}='{value}': {e}") from e
        
        return value

    def str(self, key: str, default: Any = None) -> str:
        val = self.get(key, default=default)
        if val is None:
             return None 
        return str(val)

    def int(self, key: str, default: Any = None) -> int:
        return self.get(key, default=default, cast=int)

    def float(self, key: str, default: Any = None) -> float:
        return self.get(key, default=default, cast=float)

    def bool(self, key: str, default: Any = None) -> bool:
        return self.get(key, default=default, cast=to_bool)

    def list(self, key: str, default: Any = None, delimiter: str = ",") -> List[str]:
        return self.get(key, default=default, cast=lambda v: to_list(v, delimiter))

    def json(self, key: str, default: Any = None) -> Any:
        return self.get(key, default=default, cast=to_json)

    def url(self, key: str, default: Any = None) -> ParseResult:
        return self.get(key, default=default, cast=to_url)

    def path(self, key: str, default: Any = None) -> Path:
        return self.get(key, default=default, cast=to_path)

    def alias(self, keys: List[str], default: Any = None) -> Any:
        """Try multiple keys in order."""
        for key in keys:
            val = self._get_raw(key)
            if val is not None:
                return val
        
        if default is not None:
            return default
            
        if self.strict:
             raise MissingEnvError(f"Missing required environment variables: {keys}")
        return None

    def dump(self) -> Dict[str, Any]:
        """Return a dictionary of all loaded environment variables."""
        self._check_reload()
        # Merge system and cache, system wins
        return {**self._cache, **os.environ}

    def debug(self) -> None:
        """Print all loaded environment variables."""
        print("DEBUG: Loaded Environment Variables")
        print("-" * 40)
        
        all_vars = self.dump()
        
        for key in sorted(all_vars.keys()):
            print(f"{key}={all_vars[key]}")
        print("-" * 40)
