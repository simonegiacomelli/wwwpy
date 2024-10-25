"""This module contains the HTML string manipulator functions."""
from __future__ import annotations

from enum import Enum
from html import escape
from wwwpy.common.designer.html_locator import NodePath, IndexPath, check_node_path
from wwwpy.common.designer import html_locator


class Position(str, Enum):
    inside = 'inside'
    beforebegin = 'beforebegin'
    afterend = 'afterend'


def html_add(html: str, add: str, node_path: NodePath, position: Position) -> str:
    """This function adds an HTML piece to the specified position in the HTML string."""

    start, end = html_locator.locate_span(html, node_path)

    index = start if position == Position.beforebegin else end

    return html[:index] + add + html[index:]


def html_add_indexed(html: str, add: str, index_path: IndexPath, position: Position) -> str:
    check_node_path(index_path)
    """This function adds an HTML piece to the specified position in the HTML string."""

    start, end = html_locator.locate_span_indexed(html, index_path)

    index = start if position == Position.beforebegin else end

    return html[:index] + add + html[index:]


def html_edit(html: str, edit: str, node_path: NodePath) -> str:
    """This function edits the HTML string at the specified path."""
    start, end = html_locator.locate_span(html, node_path)

    return html[:start] + edit + html[end:]


def html_edit_indexed(html: str, edit: str, index_path: NodePath) -> str:
    check_node_path(index_path)
    """This function edits the HTML string at the specified path."""
    start, end = html_locator.locate_span_indexed(html, index_path)

    return html[:start] + edit + html[end:]


def html_attribute_set(html: str, node_path: NodePath, attr_name: str, attr_value: str | None) -> str:
    """This function sets an attribute of the specified node in the HTML string.
    When the value is None, the attribute value is remove entirely"""

    node = html_locator.locate_node(html, node_path)
    if node is None:
        print(f'node not found at path={node_path} in html=```{html}```')
        return html

    cst_attr = node.cst_attribute(attr_name)
    attr_present = cst_attr is not None
    value_present = attr_present and cst_attr.value_span is not None
    spacer = ' ' if not attr_present else ''
    sep = '"' if not value_present else html[cst_attr.value_span[0]]

    value_part = '' if attr_value is None else '=' + sep + escape(attr_value) + sep

    x = cst_attr.name_span[0] if attr_present else node.attr_span[1]
    y = cst_attr.value_span[1] if value_present else (x if not attr_present else cst_attr.name_span[1])
    left = html[:x]
    right = html[y:]

    return left + spacer + attr_name + value_part + right


def html_attribute_remove(html: str, node_path: NodePath, attr_name: str) -> str:
    node = html_locator.locate_node(html, node_path)
    if node is None:
        return html

    cst_attr = node.cst_attribute(attr_name)
    if cst_attr is None:
        return html

    value_present = cst_attr.value_span is not None

    x = cst_attr.name_span[0]
    y = cst_attr.value_span[1] if value_present else cst_attr.name_span[1]
    left = html[:x]
    right = html[y:]

    return left + right
