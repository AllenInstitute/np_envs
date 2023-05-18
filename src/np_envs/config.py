from __future__ import annotations

import pathlib
import sys

import np_config

CONFIG = np_config.fetch('/projects/np_envs')
ENVS: dict[str, str] = CONFIG['envs']
ROOT = pathlib.Path(CONFIG['root']) / ('win' if sys.platform == 'win32' else 'unix')
PIP_CONFIG = CONFIG['pip_ini']
DEFAULT_PYTHON_VERSION = CONFIG.get('default_python_version', '3.8.*')

def add_env(env_name: str):
    np_config.to_zk(np_config.merge(CONFIG, {'envs': env_name}), '/projects/np_envs')