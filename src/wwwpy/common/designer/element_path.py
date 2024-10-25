from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any

from wwwpy.common.designer.html_locator import NodePath, locate_span
from wwwpy.common.modlib import _find_module_root
from wwwpy.common import modlib
from enum import Enum


class Origin(str, Enum):
    source = 'source'
    """The original html source in the component"""
    live = 'live'
    """The live html in the browser"""


@dataclass()
class ElementPath:
    """Contains the path to an element relative to a Component.
    This is intended to be serialized"""

    class_module: str
    """The module name of the Component."""
    class_name: str
    """The class name of the Component."""
    path: NodePath
    """The path from the Component (excluded) to the element."""

    origin: Origin

    @property
    def tag_name(self) -> str:
        """The tag name of the element in lowercase."""
        if len(self.path) == 0:
            return ''
        return self.path[-1].tag_name

    @property
    def data_name(self) -> Optional[str]:
        """The name of the element in the data dictionary."""
        if len(self.path) == 0:
            return None
        return self.path[-1].attributes.get('data-name', None)

    def valid(self) -> bool:
        from wwwpy.common.designer import code_strings as cs, html_parser as hp, html_locator as hl
        html = cs.html_from(self.class_module, self.class_name)
        if not html:
            return False
        return hl.locate_span(html, self.path) is not None
