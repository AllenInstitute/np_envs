from __future__ import annotations

import pathlib
import sys
from typing import Any

import np_config
import np_logging

logger = np_logging.getLogger(__name__)

ZK_CONFIG_NODE = '/projects/np_envs' 
CONFIG = np_config.fetch(ZK_CONFIG_NODE)

ROOT = pathlib.Path(CONFIG['root'])
"""Root folder for all envs on all platforms."""""
PLATFORM_ROOT = ROOT / ('win' if sys.platform == 'win32' else 'unix')
"""OS-specific root folder for all envs on this platform."""
REQUIREMENTS_TXT_ROOT = PLATFORM_ROOT / CONFIG['requirements_txt_dir_relative_to_root']
"""Where pip requirements are stored. Might not be possible to store in yaml
for ZooKeeper, so we just use txt files"""

PROJECT_TO_PIP_CONFIG: dict[str, dict] = CONFIG['pip_ini']
PROJECT_TO_PYTHON_VERSION: dict[str, str] = CONFIG['python_versions']
DEFAULT_PYTHON_VERSION = PROJECT_TO_PYTHON_VERSION['default']
"""Should be compatible with the most common `np_*` packages in use."""

def add_or_update_config(new_config: dict[str, Any]) -> None:
    logger.debug('Adding or updating %s in ZooKeeper node %s', new_config, ZK_CONFIG_NODE)
    np_config.to_zk(np_config.merge(CONFIG, new_config), ZK_CONFIG_NODE)
    logger.info('Updated ZooKeeper config')
    
def add_default_python_version(env_name: str, python_version: str) -> None:
    add_or_update_config({'python_versions': {env_name: python_version}})