from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Attribute:
    name: str
    type: str
    default: str


@dataclass
class Method:
    name: str
    def_lineno: int
    code_lineno: int
    is_async: bool = field(default=False)


@dataclass
class ClassInfo:
    name: str
    attributes: List[Attribute]
    methods: List[Method] = field(default_factory=list)

    methods_by_name: Dict[str, Method] = field(init=False)
    attributes_by_name: Dict[str, Attribute] = field(init=False)

    def __post_init__(self):
        self.methods_by_name = {method.name: method for method in self.methods}
        self.attributes_by_name = {attr.name: attr for attr in self.attributes}

    def next_attribute_name(self, base_name):
        fixed = _kebab_to_camel(base_name)
        used = set([attr.name for attr in self.attributes])
        for i in range(1, sys.maxsize):
            name = f'{fixed}{i}'
            if name not in used:
                return name
        raise ValueError('Really?')

def _kebab_to_camel(s: str) -> str:
    parts = s.split('-')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def class_info(python_source: str, class_name: str) -> ClassInfo | None:
    classes = info(python_source).classes
    filtered_classes = [clazz for clazz in classes if clazz.name == class_name]
    if len(filtered_classes) == 0:
        return None
    return filtered_classes[0]


@dataclass
class Info:
    classes: List[ClassInfo]


def info(python_source: str) -> Info:
    tree = ast.parse(python_source)
    extractor = _ClassInfoExtractor()
    extractor.visit(tree)
    return Info(extractor.classes)


class _ClassInfoExtractor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node):
        class_name = node.name
        attributes = []
        methods = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                attr_name = item.target.id
                attr_type = self.get_annotation_type(item.annotation)
                default = ast.unparse(item.value) if item.value else None
                attributes.append(Attribute(attr_name, attr_type, default))
            elif isinstance(item, ast.FunctionDef):
                methods.append(Method(item.name, item.lineno, item.body[0].lineno))
            elif isinstance(item, ast.AsyncFunctionDef):
                methods.append(Method(item.name, item.lineno, item.body[0].lineno, True))
        self.classes.append(ClassInfo(class_name, attributes, methods))
        self.generic_visit(node)

    def get_annotation_type(self, annotation):
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            names = []
            while isinstance(annotation, ast.Attribute):
                names.append(annotation.attr)
                annotation = annotation.value
            if isinstance(annotation, ast.Name):
                names.append(annotation.id)
            names.reverse()
            return '.'.join(names)
        else:
            return 'Unknown'
