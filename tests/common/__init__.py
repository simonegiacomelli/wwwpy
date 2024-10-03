import sys
from pathlib import Path

import pytest


@pytest.fixture
def restore_sys_path():
    sys_path = sys.path.copy()
    sys_meta_path = sys.meta_path.copy()
    try:
        yield
    finally:
        sys.path = sys_path
        sys.meta_path = sys_meta_path


@pytest.fixture
def dyn_sys_path(tmp_path: Path):
    sys.path.insert(0, str(tmp_path))
    pu = DynSysPath(tmp_path)
    try:
        yield pu
    finally:
        sys.path.remove(str(tmp_path))
        import wwwpy.common.reloader as r
        r.unload_path(str(tmp_path))


class DynSysPath:
    def __init__(self, path: Path):
        self.path = path

    def write_module(self, package: str, module: str, content: str):
        if not module.endswith('.py'):
            module += '.py'
        # split package into parts and create directories and __init__.py files
        parts = package.split('.')
        for i in range(0, len(parts)):
            folder = self.path / '/'.join(parts[:i + 1])
            folder.mkdir(exist_ok=True)
            ini = folder / '__init__.py'
            if not ini.exists():
                ini.touch()
        # create module file
        module_path = self.path / '/'.join(parts) / module
        module_path.write_text(content)
        return module_path
