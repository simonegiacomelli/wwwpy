import logging
import sys

from wwwpy.common import modlib

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
    print(f' File "{path}", line {lineno}')


async def server_console_log(message: str):
    print(message)
