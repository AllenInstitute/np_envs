"""
>>> env = EnvPath('np_pipeline_qc')
>>> env.conda

>>> env = EnvPath('np_pipeline_qc', python_version='3.10.5')
>>> env.venv.pip_cache == env.conda.pip_cache
True
"""
from __future__ import annotations

import configparser
import pathlib
import subprocess
import sys

import np_config 

import np_envs.config as config

ON_WINDOWS: bool = sys.platform == 'win32'

class EnvPython:
    
    project_root: pathlib.Path
    
    root: pathlib.Path
    python: pathlib.Path
    version: str = config.DEFAULT_PYTHON_VERSION
    """Python version, e.g. '3.8.5' or '3.8.*'"""
    
    def __init__(self, project_root: pathlib.Path, python_version: str | None = None, **kwargs):
        if python_version is not None:
            self.version = python_version
        self.project_root = np_config.normalize_path(project_root)
        
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.root})'
    
    @property
    def name(self) -> str:
        return self.project_root.name

    @property
    def root(self) -> pathlib.Path:
        return self.project_root / self.version.split('.*')[0] # can't have `*` in path
    
    def create(self, *args, **kwargs) -> None:
        raise NotImplementedError
    
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError
    
    
class PipManaged(EnvPython):
    
    def create(self, *args, **kwargs) -> None:
        if self.python.exists():
            print(f'{self} already exists at {self.root}')
            return
        self.run_create_cmd(*args, **kwargs)
        self.add_pip_config()
    
    def run_create_cmd(self, python_version: str, *args, **kwargs) -> None:
        raise NotImplementedError
    
    @property
    def pip_ini(self) -> pathlib.Path:
        return self.root / 'pip.ini'

    @property
    def pip_cache(self) -> pathlib.Path:
        return self.root.parent / 'pip_cache'
    
    @property 
    def pip_ini_config(self) -> configparser.ConfigParser:
        pip_ini_config = configparser.ConfigParser()
        pip_ini_config.read_dict(
            config.PIP_CONFIG.get(self.name),
            config.PIP_CONFIG['default'],
        )
        pip_ini_config.set('global', 'cache-dir', np_config.normalize_path(self.pip_cache).as_posix())
        return pip_ini_config
    
    def add_pip_config(self):
        if not self.root.exists():
            raise FileNotFoundError(f'Cannot add pip config: {self.root} does not exist')
        if not self.pip_ini.parent.exists():
            self.pip_ini.parent.mkdir(parents=True)
        with open(self.pip_ini, 'w') as f:
            self.pip_ini_config.write(f)

    @property
    def requirements(self) -> pathlib.Path:
        return pathlib.Path(__file__).parent / 'requirements' / f'{self.name}.requirements.txt'
        
    def update(self, requirements: pathlib.Path | None = None, **kwargs) -> None:
        if requirements is None:
            requirements = self.requirements
        if not requirements.exists():
            raise FileNotFoundError(f'Cannot update {self}: {requirements} does not exist')
        self.add_pip_config()
        self.run_update_cmd(requirements, **kwargs)

    def run_update_cmd(self, requirements: pathlib.Path) -> None:
        subprocess.run(f'{self.python} -m pip install -r {requirements}', check=True)
    
    
class Conda(PipManaged):
    
    @property
    def root(self) -> pathlib.Path:
        return super().root / 'conda'
    
    @property
    def python(self) -> pathlib.Path:
        return self.root / 'python.exe' if ON_WINDOWS else self.root / 'bin' / 'python'
    
    def run_create_cmd(self, *args, **kwargs) -> None:
        subprocess.run(
            f'conda create -p {self.root} python={self.version} -y --copy --no-shortcuts {" ".join(args)}',
            check=True,
            )
    
    
class Venv(PipManaged):    
    
    @property
    def root(self) -> pathlib.Path:
        return super().root / '.venv'
    
    @property
    def python(self) -> pathlib.Path:
        return self.root / 'Scripts' / 'python.exe' if ON_WINDOWS else self.root / 'bin' / 'python'
    
    def run_create_cmd(self, *args, **kwargs) -> None:
        # we need a python version to create the venv
        # pyenv would be lighter weight, but it's not usually available on windows
        conda_env = Conda(self.project_root, self.version)
        if not conda_env.python.exists():
            conda_env.create('--no-default-packages')
        subprocess.run(
            f'{conda_env.python} -m venv --copies {self.root} {" ".join(args)}',
            check=True,
            )

    
class EnvPath(pathlib.WindowsPath if ON_WINDOWS else pathlib.PosixPath): # type: ignore
    """
    >>> env = EnvPath('np_pipeline_qc')
    """
    
    _conda: Conda | None = None
    _venv: Venv | None = None
    
    version: str = config.DEFAULT_PYTHON_VERSION
    
    def __new__(cls, env_name: str, **kwargs):
        path = config.ROOT / env_name
        if not path.exists():
            print(f'Env {env_name} does not exist: build with `self.venv_create("3.8.*")')
        return super().__new__(cls, path, **kwargs)
    
    def __init__(self, path: pathlib.Path, python_version: str | None = None):
        if python_version is not None:
            self.version = python_version
            
    def __repr__(self) -> str:
        return super().__repr__()
    
    @property
    def python(self) -> pathlib.Path:
        return self.venv.python if self.venv.python.exists() else self.conda.python
    
    @property
    def conda(self) -> Conda:
        if not self._conda:
            self._conda = Conda(self, self.version)
        return self._conda
    
    @property
    def venv(self) -> Venv:
        if not self._venv:
            self._venv = Venv(self, self.version)
        return self._venv
    
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()