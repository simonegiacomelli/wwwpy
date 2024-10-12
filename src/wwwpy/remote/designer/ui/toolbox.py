from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Tuple, List

import js
import wwwpy.remote.component as wpc
from js import document, console, Event, HTMLElement, window
from pyodide.ffi import create_proxy
from wwwpy.common import state, modlib
from wwwpy.common.designer import element_library, new_component
from wwwpy.common.designer.code_edit import add_component, ElementDef
from wwwpy.common.designer.element_library import Help
from wwwpy.common.designer.element_path import ElementPath
from wwwpy.common.designer.html_edit import Position
from wwwpy.remote import dict_to_js, set_timeout
from wwwpy.remote.designer import element_path
from wwwpy.remote.designer.drop_zone import DropZone
from wwwpy.remote.designer.global_interceptor import GlobalInterceptor, InterceptorEvent
from wwwpy.remote.designer.ui.draggable_component import DraggableComponent
from wwwpy.server.designer import rpc

from wwwpy.remote.designer.helpers import _element_lbl, _help_button, info_link, _help_url
from wwwpy.remote.designer.ui.property_editor import PropertyEditor
from . import filesystem_tree
from .help_icon import HelpIcon  # noqa
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolboxState:
    geometry: Tuple[int, int, int, int] = field(default=(100, 30, 400, 330))
    toolbox_search: str = ''
    selected_element_path: Optional[ElementPath] = None


@dataclass
class MenuMeta:
    label: str
    html: str
    always_visible: bool = False
    p_element: js.HTMLElement = None
    help: Help = None


def menu(label, always_visible=False):
    def wrapped(fn, label=label):
        help = None
        if isinstance(label, Help):
            help = label
            label = label.description
        fn.label = label
        fn.meta = MenuMeta(label, label, always_visible, help=help)
        return fn

    return wrapped


class ToolboxComponent(wpc.Component, tag_name='wwwpy-toolbox'):
    body: HTMLElement = wpc.element()
    inputSearch: js.HTMLInputElement = wpc.element()
    dragComp1: DraggableComponent = wpc.element()
    property_editor: PropertyEditor = wpc.element()
    _select_element_btn: js.HTMLElement = wpc.element()
    _select_clear_btn: js.HTMLElement = wpc.element()
    components_marker = '-components-'

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
<style>
.two-column-layout {
  display: flex;
  flex-wrap: wrap;
}

.two-column-layout p {
  width: calc(50% - 10px); /* 50% width minus half of the gap */
  margin: 0 20px 10px 0; /* Right margin creates gap between columns */
}

.two-column-layout p:nth-child(even) {
  margin-right: 0; /* Removes right margin for every even child */
}
</style>     
<wwwpy-draggable-component data-name='dragComp1'>
    <div slot='title' style='text-align: center'>wwwpy</div>
    <div  style="text-align: center; padding: 8px">     
        <button data-name="_select_element_btn">Select element...</button>   
        <button data-name="_select_clear_btn">Clear selection</button>   
        <wwwpy-property-editor data-name="property_editor"></wwwpy-property-editor>        
        <p><input data-name='inputSearch' type='search' placeholder='type to filter...'></p>
        <div data-name='body' class='two-column-layout'></div>
    </div>   
</wwwpy-draggable-component>         
"""
        self._manage_toolbox_state()

        attrs = [v for k, v in vars(self.__class__).items() if hasattr(v, 'label')]
        self._all_items: List[MenuMeta] = []

        def add_p(menu_meta: MenuMeta, callback):  # callback can be async
            self._all_items.append(menu_meta)
            p: js.HTMLElement = document.createElement('p')
            p.style.color = 'white'
            menu_meta.p_element = p
            p.innerHTML = menu_meta.html
            p.addEventListener('click', create_proxy(callback))

        def add_comp(element_def: ElementDef):

            def _on_pointed(drop_zone: DropZone | None):
                console.log(f'pointed dropzone: {drop_zone}')
                msg = (f'Insert new {element_def.tag_name}')
                if drop_zone:
                    pos = 'before' if drop_zone.position == Position.beforebegin else 'after'
                    # msg += f' at {drop_zone.position.name} of {drop_zone.element.tagName}'
                    msg += f' {pos} {drop_zone.element.tagName}'
                else:
                    msg += ' ... select a dropzone.'
                self.property_editor.message1div.innerHTML = msg

            async def _start_drop_for_comp(event):
                _on_pointed(None)
                res = await _drop_zone_start_selection_async(_on_pointed)
                logger.debug(f'_start_drop_for_comp res={res}')
                if res:
                    await self._process_dropzone(res, element_def)
                else:
                    self.property_editor.message1div.innerHTML = 'canceled'

            element_html = f'<span style="cursor: pointer">{element_def.tag_name}</span> {_help_button(element_def)}'
            add_p(MenuMeta(element_def.tag_name, element_html), _start_drop_for_comp)

        for member in attrs:
            if member.meta.label == self.components_marker:
                [add_comp(ele_def) for ele_def in element_library.element_library().elements]
            else:
                help = member.meta.help
                if help:
                    help_html = '' if not help.url else info_link(help.url)
                    element_html = f'{help.description} {help_html}'
                    add_p(MenuMeta(help.description, element_html), partial(member, self))
                else:
                    add_p(member.meta, partial(member, self))
        self._update_toolbox_elements()

    async def _process_dropzone(self, drop_zone: DropZone, element_def: ElementDef):
        el_path = element_path.element_path(drop_zone.element)

        if not el_path:
            window.alert(f'No component found for dropzone!')
            return

        logger.debug(f'element_path={el_path}')
        file = modlib._find_module_path(el_path.class_module)
        old_source = file.read_text()

        add_result = add_component(old_source, el_path.class_name, element_def, el_path.path, drop_zone.position)

        if add_result:
            logger.debug(f'write_module_file len={len(add_result.html)} el_path={el_path}')
            new_element_path = ElementPath(el_path.class_module, el_path.class_name, add_result.node_path)
            self._toolbox_state.selected_element_path = new_element_path
            write_res = await rpc.write_module_file(el_path.class_module, add_result.html)
            logger.debug(f'write_module_file res={write_res}')

    def _manage_toolbox_state(self):
        self._toolbox_state = state._restore(ToolboxState)
        self.inputSearch.value = self._toolbox_state.toolbox_search
        self.dragComp1.set_geometry(self._toolbox_state.geometry)

        def on_toolbar_geometry_change():
            if self.dragComp1.acceptable_geometry():
                self._toolbox_state.geometry = self.dragComp1.geometry()

        self.dragComp1.geometry_change_listeners.append(on_toolbar_geometry_change)
        self._restore_selected_element_path()

    def inputSearch__input(self, e: Event):
        self._toolbox_state.toolbox_search = self.inputSearch.value
        self._update_toolbox_elements()

    def _update_toolbox_elements(self):
        self.body.innerHTML = ''
        for meta in self._all_items:
            p = meta.p_element
            if meta.always_visible or self.inputSearch.value.lower() in meta.label.lower():
                self.body.appendChild(p)

    # @menu('Reload')
    # def _hot_reload(self, e: Event):
    #     _reload()
    async def _select_element_btn__click(self, e: Event):
        await self._select_component(e)

    async def _select_clear_btn__click(self, e: Event):
        self._toolbox_state.selected_element_path = None
        self._restore_selected_element_path()

    # @menu('Select component...', always_visible=True)
    async def _select_component(self, e: Event):
        no_comp = 'Click an element...'
        self.property_editor.message1div.innerHTML = no_comp

        def _on_pointed(drop_zone: DropZone | None):
            msg = no_comp
            if drop_zone:
                msg = 'Click to select ' + _element_lbl(drop_zone.element)
            self.property_editor.message1div.innerHTML = msg
            console.log(f'pointed dropzone: {drop_zone}')

        res = await _drop_zone_start_selection_async(_on_pointed, whole=True)
        self._toolbox_state.selected_element_path = element_path.element_path(res.element) if res else None
        self._restore_selected_element_path()

    @menu(components_marker)
    def _drop_zone_start(self, e: Event):
        assert False, 'Just a placeholder'

    @menu(Help('Create new component', _help_url('add_component')))
    async def _add_new_component(self, e: Event):
        if js.window.confirm('Add new component file?\nIt will be added to your "remote" folder.'):
            res = await rpc.add_new_component()
            js.window.alert(res)

    @menu(Help("Explore local filesystem", _help_url('remote_filesystem')))
    async def _browse_local_filesystem(self, e: Event):
        filesystem_tree.show_explorer()

    # @menu('handle global click')
    def _handle_global_click(self, e: Event):
        # add input
        def global_click(event: Event):
            event.preventDefault()
            event.stopImmediatePropagation()
            event.stopPropagation()
            console.log('global click', event.element)
            if self._global_click:
                document.removeEventListener('click', self._global_click, True)
                self._global_click = None

        self._global_click = create_proxy(global_click)
        document.addEventListener('click', self._global_click, True)

    def _restore_selected_element_path(self):
        element_path = self._toolbox_state.selected_element_path
        if element_path:
            console.log(f'restoring selected element path: {element_path}')
            if not element_path.valid():
                element_path = None

        self.property_editor.selected_element_path = element_path
        if element_path:
            self._select_clear_btn.removeAttribute('disabled')
        else:
            self._select_clear_btn.setAttribute('disabled', '')


def is_inside_toolbar(element: HTMLElement | None):
    if not element:
        return False

    orig = element
    # loop until the root element and see if it is the toolbar
    res = False
    while element:
        if element.tagName.lower() == ToolboxComponent.component_metadata.tag_name:
            res = True
            break
        element = element.parentElement

    return res


def _default_drop_zone_accept(drop_zone: DropZone):
    name = drop_zone.element.tagName.lower()
    accept = not (name == 'body' or name == 'html' or name == ToolboxComponent.component_metadata.tag_name)
    return accept


async def _drop_zone_start_selection_async(on_pointed, whole=False) -> Optional[DropZone]:
    from wwwpy.remote.designer.drop_zone import drop_zone_selector

    event = asyncio.Event()
    result = []

    def intercept_ended(ev: InterceptorEvent):
        selected = drop_zone_selector.stop()
        if is_inside_toolbar(ev.target):
            ev.uninstall()
            event.set()
            return
        ev.preventAndStop()
        if selected:
            ev.uninstall()
            console.log(
                f'selection accepted position {selected.position.name} target: ', selected.element,
                'parent: ', selected.element.parentElement,
                'event: ', ev.event,
                'composedPath: ', ev.event.composedPath(),
            )
            result.append(selected)
            event.set()

    GlobalInterceptor(intercept_ended, 'pointerdown').install()

    click_inter = GlobalInterceptor(lambda ev: ev.preventAndStop(), 'click')
    click_inter.install()
    drop_zone_selector.start_selector(on_pointed, _default_drop_zone_accept, whole=whole)
    await event.wait()
    set_timeout(lambda: click_inter.uninstall(), 500)

    if len(result) == 0:
        return None

    return result[0]
