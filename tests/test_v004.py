import pytest
import os
from pathlib import Path
from envplus import Env

def test_variable_expansion(tmp_path):
    f = tmp_path / ".env"
    f.write_text("HOST=localhost\nPORT=8000\nURL=http://${HOST}:${PORT}/api")
    
    env = Env(env_file=str(f))
    assert env.str("URL") == "http://localhost:8000/api"

def test_expansion_with_system_env(tmp_path, clean_env):
    os.environ["USER"] = "admin"
    f = tmp_path / ".env"
    f.write_text("WELCOME_MSG=Hello ${USER}")
    
    env = Env(env_file=str(f))
    assert env.str("WELCOME_MSG") == "Hello admin"

def test_multiple_files(tmp_path):
    f1 = tmp_path / ".env"
    f1.write_text("A=1\nB=2")
    
    f2 = tmp_path / ".env.local"
    f2.write_text("B=3\nC=4")
    
    env = Env(env_file=[str(f1), str(f2)])
    assert env.int("A") == 1
    assert env.int("B") == 3 # Overridden
    assert env.int("C") == 4

def test_url_type(tmp_path):
    f = tmp_path / ".env"
    f.write_text("API_URL=https://api.example.com/v1")
    
    env = Env(env_file=str(f))
    url = env.url("API_URL")
    assert url.scheme == "https"
    assert url.netloc == "api.example.com"
    assert url.path == "/v1"

def test_path_type(tmp_path):
    f = tmp_path / ".env"
    f.write_text(f"LOG_DIR={str(tmp_path)}")
    
    env = Env(env_file=str(f))
    path = env.path("LOG_DIR")
    assert isinstance(path, Path)
    assert path == tmp_path

def test_dump(tmp_path, clean_env):
    os.environ["SYS_VAR"] = "sys"
    f = tmp_path / ".env"
    f.write_text("FILE_VAR=file")
    
    env = Env(env_file=str(f))
    dump = env.dump()
    
    assert dump["SYS_VAR"] == "sys"
    assert dump["FILE_VAR"] == "file"
