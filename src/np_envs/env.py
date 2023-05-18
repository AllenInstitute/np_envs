from __future__ import annotations

import configparser
import pathlib
import subprocess
import sys

import np_envs.config as config

class EnvPath(pathlib.WindowsPath if sys.platform == 'win32' else pathlib.PosixPath):
    """
    >>> env = EnvPath('np_pipeline_qc')
    """
    
    def __new__(cls, env_name: str, **kwargs):
        path = config.ROOT / env_name
        if not path.exists():
            print(f'Env {env_name} does not exist: build with `self.venv_create("3.8.*")')
        return super().__new__(cls, path, **kwargs)
    
    def __repr__(self) -> str:
        return super().__repr__()
    
    @property
    def venv_root(self) -> pathlib.Path:
        return self / '.venv'
    
    @property
    def conda_root(self) -> pathlib.Path:
        return self
    
    @property
    def venv_python(self) -> pathlib.Path:
        return self.venv_root / 'Scripts' / 'python.exe' if sys.platform == 'win32' else self / 'bin' / 'python'
    
    @property
    def venv_cache(self) -> pathlib.Path:
        return self.venv_root / 'pip_cache'
    
    @property
    def conda_python(self) -> pathlib.Path:
        return self.conda_root / 'python.exe' if sys.platform == 'win32' else self / 'bin' / 'python'
    
    @property
    def requirements(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent / 'requirements' / f'{self.name}.requirements.txt'
    
    def conda_create(self, python_version: str | None) -> None:
        if not python_version:
            python_version = config.DEFAULT_PYTHON_VERSION
        if self.conda_python.exists():
            print(f'Conda env already exists at {self}')
            return
        subprocess.run(
            f'conda create -n {self.name} python={python_version} -p {self}',
            check=True,
            )
        config.add_env(self.name)
        self.add_pip_config()
        
    def venv_create(self, python_version: str | None, **kwargs) -> None:
        if not python_version:
            python_version = config.DEFAULT_PYTHON_VERSION
        if self.venv_python.exists():
            print(f'Venv already exists at {self}')
        if not self.conda_python.exists():
            self.conda_create(python_version)
        subprocess.run(f'{self.conda_python} -m venv --copies {self.venv_root}', check=True)
        self.venv_update(kwargs.get('requirements'))
        
    def pip_ini_config(self) -> configparser.ConfigParser:
        pip_ini_config = configparser.ConfigParser()
        pip_ini_config.read_dict(
            config.PIP_CONFIG.get(self.name),
            config.PIP_CONFIG['default'],
        )
        pip_ini_config.set('global', 'cache-dir', str(self.venv_cache))
        return pip_ini_config
    
    def add_pip_config(self):
        for root in (self.conda_root, self.venv_root):
            if root.exists():
                with open(root / 'pip.ini', 'w') as f:
                    self.pip_ini_config().write(f)
    
    def venv_update(self, requirements: pathlib.Path | None = None, **kwargs) -> None:
        self.add_pip_config()
        if not requirements:
            requirements = self.requirements
        if not requirements.exists():
            print(f'No requirements file found at {requirements}')
            return
        subprocess.run(f'{self.venv_python} -m pip install -r {requirements}', check=True)

if __name__ == '__main__':
    import doctest
    doctest.testmod()