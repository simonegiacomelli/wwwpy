from typing import Callable

import libcst as cst


def html_string_edit(source_code: str, html_manipulator: Callable[[str], str]) -> str:
    tree = cst.parse_module(source_code)
    transformer = _HTMLStringUpdater(html_manipulator)
    modified_tree = tree.visit(transformer)
    return modified_tree.code


class _HTMLStringUpdater(cst.CSTTransformer):
    def __init__(self, html_manipulator: Callable[[str], str]):
        super().__init__()
        self.html_manipulator = html_manipulator

    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.CSTNode:
        if original_node.value.startswith('"""') and original_node.value.endswith('"""'):
            original_html = original_node.value[3:-3]
            modified_html = self.html_manipulator(original_html)
            return updated_node.with_changes(value=f'"""{modified_html}"""')
        return updated_node
