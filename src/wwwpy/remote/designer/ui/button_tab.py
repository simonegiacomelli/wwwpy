from __future__ import annotations

from typing import List, Union, Callable

import wwwpy.remote.component as wpc
import js
from wwwpy.remote import dict_to_js
from pyodide.ffi import create_proxy


class ButtonTab(wpc.Component, tag_name='wwwpy-button-tab'):
    _root: js.HTMLElement = wpc.element()

    @property
    def tabs(self) -> List[Tab]:
        return self._tabs

    @tabs.setter
    def tabs(self, value: List[Union[str, Tab]]):
        def process(v):
            if not isinstance(v, Tab):
                v = Tab(v)
            v.parent = self
            return v

        self._tabs = [process(v) for v in value]
        re = self._root
        re.innerHTML = ''
        for tab in self._tabs:
            re.appendChild(tab.root_element())

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
<style>
  .selected {
        box-shadow: 0 0 0 2px darkgray;
        }
</style>
<span data-name="_root"></span>
"""
        style = self._root.style
        style.display = 'flex'
        style.justifyContent = 'space-around'
        style.width = '100%'

        self._tabs = []

    def _tab_selected(self, tab: Tab):
        for t in self._tabs:
            t.selected = t == tab


_selected_default = lambda tab: None


class Tab:
    parent: ButtonTab

    def __init__(self, text: str = '', on_selected: Callable[[Tab], None] = _selected_default):
        self.text = text
        self.on_selected = on_selected
        self._root_element: js.HTMLElement = None

    def do_click(self, *event):
        self.parent._tab_selected(self)
        self.on_selected(self)

    def root_element(self) -> js.HTMLElement:
        if self._root_element is None:
            div = js.document.createElement('button')
            div.textContent = self.text
            div.addEventListener('click', create_proxy(self.do_click))
            self._root_element = div
        return self._root_element

    @property
    def selected(self) -> bool:
        return self.root_element().classList.contains('selected')

    @selected.setter
    def selected(self, value: bool):
        if value:
            self.root_element().classList.add('selected')
        else:
            self.root_element().classList.remove('selected')
