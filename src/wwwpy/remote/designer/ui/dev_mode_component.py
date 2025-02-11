from __future__ import annotations

import js

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from wwwpy.server.designer import rpc
from . import quickstart_ui
from .quickstart_ui import QuickstartUI
from .toolbox import ToolboxComponent
import logging

logger = logging.getLogger(__name__)


def show():
    x = DevModeComponent.instance
    js.document.body.append(DevModeComponent.instance.element)


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class DevModeComponent(wpc.Component, tag_name='wwwpy-dev-mode-component'):
    toolbox: ToolboxComponent = wpc.element()
    quickstart: QuickstartUI | None = None
    _instance: DevModeComponent

    @classproperty
    def instance(cls) -> DevModeComponent:  # noqa
        try:
            _i = cls._instance
            logger.warning(f'instance found: {_i}')
        except AttributeError:
            _i = DevModeComponent()
            cls._instance = _i
            logger.warning(f'instance created: {_i}')
        return _i

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<wwwpy-toolbox data-name="toolbox"></wwwpy-toolbox>        
        """

    async def after_init_component(self):
        if await rpc.quickstart_possible():
            self.quickstart = quickstart_ui.create()
            def _on_done(): self.toolbox.visible = True
            self.quickstart.on_done = lambda *_: _on_done()
            self.element.shadowRoot.append(self.quickstart.window.element)
            self.toolbox.visible = False
