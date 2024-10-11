import logging
import sys

from wwwpy.common import modlib
from wwwpy.common.designer import new_component

logger = logging.getLogger(__name__)


async def write_module_file(module: str, content: str) -> str:
    msg = f'write_module_file module={module} content len={len(content)}'
    logger.debug(msg)
    path = modlib._find_module_path(module)
    if not path:
        raise ValueError(f'Cannot find module {module}')
    path.write_text(content)
    return f'done {msg}'


def _fix_stacktrace(message: str):
    return message.replace('"/wwwpy_bundle/', '"')


async def on_error(message: str, source: str, lineno: int, colno: int, error: str):
    print(f'rpc.on_error')
    message = _fix_stacktrace(message)
    error = _fix_stacktrace(error)
    all_str = f'message==={message}\nsource==={source}\nlineno==={lineno}\ncolno==={colno}\nerror==={error}'
    print(all_str, file=sys.stderr)


async def on_unhandledrejection(message: str):
    message = _fix_stacktrace(message)
    print(message, file=sys.stderr)


async def print_module_line(module: str, message: str, lineno: int):
    #  File "remote/designer/toolbar.py", line 140, in on_changes
    path = modlib._find_module_path(module)
    if not path:
        raise ValueError(f'Cannot find module {module}')
    print(message)
    print(_ide_path_link(path, lineno))


def _ide_path_link(path, lineno):
    ide_path_link = f'  File "{path}", line {lineno}'
    return ide_path_link


async def server_console_log(message: str):
    print(message)


async def add_new_component() -> str:
    path = new_component.add()
    if path:
        print(f'Added new component')
        print(_ide_path_link(path, 1))
        return f'Added new component file:\n\n{path.name}'
    return 'Failed to add new component'
