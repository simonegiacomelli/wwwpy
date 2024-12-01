from __future__ import annotations

import js
from js import HTMLElement, console
from pyodide.ffi import create_proxy, create_once_callable

namespace = "window.python_custom_elements"


class Metadata:
    def __init__(self, tag_name: str | None = None, clazz=None):
        if clazz is not None:
            if not issubclass(clazz, Component):
                raise Exception(f'clazz must be a subclass of {Component.__name__}')
            if tag_name is None:
                # get the full class name
                fully_qualified_class_name = clazz.__qualname__
                tag_name = ('wwwpy-auto-' + fully_qualified_class_name.lower()
                            .replace('<', '-')
                            .replace('>', '-')
                            .replace('.', '-')
                            )

        self.tag_name = tag_name
        self.observed_attributes = set()
        self.registered = False
        self.clazz = clazz
        self._custom_element_class_template = None

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__name__}')
        self.clazz = owner
        # if self.auto_define:
        #     self.define_element()

    def define_element(self):
        if self.registered:
            return
        if js.eval(f'typeof {namespace}') == 'undefined':
            js.eval(namespace + ' = {}')

        js_class_name = self.tag_name.replace('-', '_').replace('.', '_')
        self._js_class_name = js_class_name

        pc = js.eval(namespace)
        already_defined = hasattr(pc, js_class_name)
        setattr(pc, js_class_name, self.clazz)  # set the python constructor, in any case
        if not already_defined:
            obs_attr = ', '.join(f'"{attr}"' for attr in self.observed_attributes)
            code = (_custom_element_class_template
                    .replace('$ClassName', js_class_name)
                    .replace('$tagName', self.tag_name)
                    .replace('$observedAttributes', obs_attr)
                    .replace('$namespace', namespace)
                    )
            self._custom_element_class_template = code
            # raise Exception(code)
            js.eval(code)

        self.registered = True


def get_component(element: HTMLElement) -> Component | None:
    if not hasattr(element, '_python_component'):
        return None
    component = element._python_component
    if hasattr(component, "unwrap"):
        component = component.unwrap()

    return component


class Component:
    component_metadata: Metadata = None
    element: HTMLElement = None
    element_not_found_raises = False

    def __init_subclass__(cls, tag_name: str | None = None, auto_define=True, **kwargs):
        super().__init_subclass__(**kwargs)
        metadata = Metadata(tag_name=tag_name, clazz=cls)
        cls.component_metadata = metadata
        if metadata.clazz is None:
            metadata.clazz = cls

        for name, value in cls.__dict__.items():
            if isinstance(value, attribute):
                cls.component_metadata.observed_attributes.add(name)

        if auto_define:
            cls.component_metadata.define_element()

    def __init__(self, element_from_js=None):
        if element_from_js is None:
            self.element = js.eval(f'window.{self.component_metadata._js_class_name}').new(create_proxy(self))
        else:
            self.element = element_from_js

        self.init_component()
        self._bind_events()

    def init_component(self):
        pass

    def connectedCallback(self):
        pass

    def disconnectedCallback(self):
        pass

    def adoptedCallback(self):
        pass

    def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
        pass

    def root_element(self):
        """This is used to locate the child elements"""
        e = self.element
        return e if e.shadowRoot is None else e.shadowRoot

    def _find_element(self, name: str):
        root = self.root_element()
        selector = root.querySelector(f'[data-name="{name}"]')
        if selector is None:
            msg = f'Not found data-name: [{name}] html: [{root.outerHTML}]'
            if self.element_not_found_raises:
                raise ElementNotFound(msg)
            else:
                console.warn(msg)

        return selector

    def _find_python_attribute(self, name: str):
        selector = self._find_element(name)

        if selector:
            comp = get_component(selector)
            if comp:
                selector = comp

        self._check_type(name, selector)
        return selector

    def _check_type(self, name, selector):
        import inspect
        annotations = inspect.get_annotations(self.__class__, eval_str=True)

        expected_type = annotations.get(name, None)
        if expected_type is None:
            # raise Exception(f'No type defined for field: {name}')
            return
        # raise Exception(f'type of expected_type: {type(expected_type)}')
        # test if expected_type is a class
        if not inspect.isclass(expected_type):
            return
        if not issubclass(expected_type, Component):
            return
        # raise Exception(f'Expected type: {expected_type} for field: {name} but found: {type(selector)}')
        isinst = not isinstance(selector, expected_type)
        # raise Exception(f'isinst: {isinst}')
        if isinst:
            raise WrongTypeDefinition(f'Expected type: {expected_type} for field: {name} but found: {type(selector)}')

    def _bind_events(self):

        members = dir(self)

        for name in members:
            if name.startswith('__'):
                continue
            parts = name.split('__')
            if len(parts) != 2:
                continue

            element_name = parts[0]
            event_name = parts[1].replace('_', '-')
            if element_name == '' or event_name == '':
                continue

            element = self._find_element(element_name)
            if element is None:
                console.warn(f'Event bind failed, element `{element_name}` was not found for method `{name}`')
                continue

            m = getattr(self, name)
            element.addEventListener(event_name, create_proxy(m))


class ElementNotFound(AttributeError): pass


class WrongTypeDefinition(TypeError): pass


# language=javascript
_custom_element_class_template = """
class $ClassName extends HTMLElement {
    static observedAttributes = [ $observedAttributes ];
    constructor(python_component) {
        super();
        if (python_component) 
            this._python_component = python_component;
        else 
            this._python_component = $namespace.$ClassName(this);
    }

    connectedCallback()    { this._python_component.connectedCallback(); }
    disconnectedCallback() { this._python_component.disconnectedCallback(); }
    adoptedCallback()      { this._python_component.adoptedCallback(); }
    attributeChangedCallback(name, oldValue, newValue) { this._python_component.attributeChangedCallback(name, oldValue, newValue); }
}

customElements.define('$tagName', $ClassName);
window.$ClassName = $ClassName;
"""


# class Attribute(str):
#     _attr: attribute
#     present: bool
#
#     def toggle(self):
#         pass


class attribute:

    def __init__(self):
        self.name = None

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__qualname__}')
        self.name = name

    def __get__(self, obj: Component, objtype=None):
        return obj.element.getAttribute(self.name)

    def __set__(self, obj: Component, value):
        obj.element.setAttribute(self.name, value)


class element:

    def __init__(self):
        self.name = None

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__qualname__}')
        self.name = name

    def __get__(self, obj: Component, objtype=None):
        return obj._find_python_attribute(self.name)
