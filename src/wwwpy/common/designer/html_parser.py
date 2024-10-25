from __future__ import annotations

from collections import UserList
from dataclasses import dataclass, field
from .html_parser_mod import HTMLParser
from typing import Tuple, Dict, List


@dataclass
class CstAttribute:
    name: str
    value: str | None
    name_span: Tuple[int, int]
    value_span: Tuple[int, int] | None
    """The span of the attribute value in the HTML string including the quotes char."""


def cst_attribute_dict(*attributes: CstAttribute) -> Dict[str, CstAttribute]:
    return {attr.name: attr for attr in attributes}


@dataclass
class CstNode:
    tag_name: str
    span: Tuple[int, int]
    """The span of the node in the HTML string, including the `<` and `>` characters."""
    attr_span: Tuple[int, int]
    """The span of the attributes part. If there is no span the tuple will contain the same value."""
    content_span: Tuple[int, int] | None = None
    """The span of the content part. If there is no content the tuple will contain the same value. 
    If the node is a void tag, this will be None."""
    children: CstTree = field(default_factory=lambda: CstTree())
    attributes_list: List[CstAttribute] = field(default_factory=list)
    html: str = field(repr=False, compare=False, default='')
    content: str | None = field(repr=False, compare=False, default=None)
    parent: CstNode | None = field(repr=False, compare=False, default=None)
    level: int = field(repr=False, compare=False, default=0)
    child_index: int = field(repr=False, compare=False, default=0)

    def __post_init__(self):
        self._attributes_dict = None

    @property
    def attributes(self) -> Dict[str, str]:
        if self._attributes_dict is None:
            self._attributes_dict = {attr.name: attr.value for attr in self.attributes_list}
        return self._attributes_dict

    def cst_attribute(self, name: str) -> CstAttribute | None:
        for attr in self.attributes_list:
            if attr.name == name:
                return attr
        return None


class CstTree(UserList[CstNode]):
    def traverse(self, indexes: list[int]) -> CstNode | None:
        children = self
        node = None
        for i in indexes:
            if i < 0 or i >= len(children):
                return None
            node = children[i]
            children = node.children
        return node


def html_to_tree(html: str) -> CstTree:
    parser = _PositionalHTMLParser(html)
    parse = parser.parse()
    _complete_tree_data(html, parse)
    return parse


class _PositionalHTMLParser(HTMLParser):
    void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

    def __init__(self, html: str):
        super().__init__()
        self.html = html
        self.nodes = CstTree()
        self.stack = []
        self.current_pos = 0

    def handle_starttag_extended(self, tag, attrs, attrs_extended, autoclosing):
        start_pos = self.current_pos

        def _cst_attr(name, v) -> CstAttribute:
            return CstAttribute(name, v['value'], v['name_span'], v['value_span'])

        text = self.get_starttag_text()
        end_displ = 2 if autoclosing else 1
        attr_span = (start_pos + len(tag) + 1, self.current_pos + len(text) - end_displ)
        node = CstNode(
            tag_name=tag,
            span=(start_pos, None),
            attr_span=attr_span,
            content_span=None if autoclosing else (attr_span[1] + 1, None),
            attributes_list=[_cst_attr(name, v) for name, v in attrs_extended.items()],
        )

        if self.stack:
            self.stack[-1].children.append(node)

        if tag not in self.void_tags:
            self.stack.append(node)
        else:
            node.span = (start_pos, self.current_pos + len(text))
            node.content_span = None
            if not self.stack:
                self.nodes.append(node)

        self.current_pos += len(text)

    def handle_endtag(self, tag):
        if tag in self.void_tags:  # a void tag with end tag
            return
        if not self.stack:
            return

        node = self.stack.pop()
        span_end = self.current_pos + len(tag) + 3  # +3 for </ and >
        node.span = (node.span[0], span_end)
        if node.content_span:
            node.content_span = (node.content_span[0], self.current_pos)
        if not self.stack:
            self.nodes.append(node)

        self.current_pos += len(tag) + 3

    def handle_data(self, data):
        self.current_pos += len(data)

    def parse(self):
        self.feed(self.html)
        return self.nodes


def _complete_tree_data(html: str, tree: CstTree, parent: CstNode | None = None, level: int = 0):
    for idx, node in enumerate(tree):
        node.parent = parent
        node.level = level
        node.child_index = idx
        start, end = node.span
        node.html = html[start:end]
        c_sp = node.content_span
        node.content = html[c_sp[0]:c_sp[1]] if c_sp else None
        _complete_tree_data(node.html, node.children, node, level + 1)
