from __future__ import annotations

from js import HTMLElement, console
from wwwpy.common.designer.element_editor import ElementEditor, EventEditor
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.designer.element_path import ElementPath
from wwwpy.remote.designer import element_path

from wwwpy.server.designer import rpc


async def _rpc_save(el_path: ElementPath, new_source: str):
    await rpc.write_module_file(el_path.class_module, new_source)


def info_link(href):
    # open in a new page
    # <a href='https://www.google.com' target='_blank'><svg class="help-icon"><use href="#help-icon"/></svg></a>
    #language=html
    return f"""<wwwpy-help-icon href="{href}"></wwwpy-help-icon>"""

    return (f'<a href="{href}" style="text-decoration: none" target="_blank">'
            f'<svg class="help-icon"><use href="#help-icon"/></svg></a>')


def _element_lbl(element: HTMLElement) -> str:
    ep = element_path.element_path(element)
    console.log(f'element_path={ep}')
    return _element_path_lbl(ep) if ep else 'No element path'


def _element_path_lbl(ep: ElementPath | None) -> str:
    lbl = '' if not ep.data_name else f' ({ep.data_name})'
    msg = f'{ep.tag_name} element {lbl} in {ep.class_name}'
    return msg


async def _log_event(element_editor: ElementEditor, event_editor: EventEditor):
    ep = element_editor.element_path
    ee = ElementEditor(ep, element_editor.element_def)
    ev = ee.events.get(event_editor.definition.name)
    console.log(f'event: {ev.definition.name} handled: {ev.method}')
    message = f'event: {ev.definition.name} handled: {ev.method}'
    await rpc.print_module_line(ep.class_module, message, ev.method.code_lineno)


def _help_button(element_def: ElementDef) -> str:
    help_url = element_def.help.url
    help_button = '' if len(help_url) == 0 else info_link(element_def.help.url)
    return help_button


async def _on_error( message, source, lineno, colno, error):
    await rpc.on_error(message, source, lineno, colno, str(error))

async def _on_unhandledrejection(event):
    await rpc.on_unhandledrejection(f'{event.reason}')

