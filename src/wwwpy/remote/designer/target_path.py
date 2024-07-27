from __future__ import annotations

import sys

from js import HTMLElement, Array, Element, document

from wwwpy.common.designer.html_locator import Node, NodePath
from wwwpy.common.designer.target_path import TargetLocation
import inspect


def _get_source_file_path(instance):
    cls = instance.__class__
    module = cls.__module__
    source_file_path = inspect.getfile(sys.modules[module])
    return source_file_path


def _fqn(obj):
    return f"{obj.__class__.__module__}.{obj.__class__.__name__}"


def target_location(target: Element) -> TargetLocation:
    """
    Compute the [TargetLocation].
    """

    path = []
    element: Element = target
    while element:
        if hasattr(element, "_py"):
            component = element._py
            return TargetLocation(component=component, path=path)
        if element == document.body:
            return TargetLocation(component=None, path=path)

        parent = element.parentNode
        child_index = Array.prototype.indexOf.call(parent.children, element) if parent else -1
        attributes = {attr.name: attr.value for attr in element.attributes}
        path.insert(0, Node(element.tagName, child_index, attributes))
        element = parent

    return TargetLocation(component=None, path=path)


def path_to_target(target: HTMLElement) -> NodePath:
    """
    Get the path from the root to the target.
    """

    path = []
    element = target
    while element:
        parent = element.parentNode
        child_index = Array.prototype.indexOf.call(parent.children, element) if parent else -1
        attributes = {attr.name: attr.value for attr in element.attributes}
        path.append(Node(element.tagName, child_index, attributes))
        element = parent
    path.reverse()
    return path
