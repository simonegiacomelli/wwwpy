from wwwpy.common.designer.code_edit import Attribute, add_component, ElementDef, add_method, \
    ensure_imports
from wwwpy.common.designer.code_edit import Attribute, add_property, add_component, add_method
from wwwpy.common.designer.code_info import info
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.html_locator import Node


def test_add_property():
    original_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btn1: HTMLButtonElement = wpc.element()
    """

    # Expected source after adding the new attribute
    expected_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btn1: HTMLButtonElement = wpc.element()
    btn2: HTMLButtonElement = wpc.element()
    """

    modified_source = add_property(original_source, 'MyElement',
                                   Attribute('btn2', 'HTMLButtonElement', 'wpc.element()'))

    modified_info = info(modified_source)
    expected_info = info(expected_source)

    assert modified_info == expected_info, "The attribute was not added correctly."


def test_add_property__should_retain_comments_and_style():
    original_source = """
import wwwpy.remote.component as wpc
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    """

    expected_source = """import js

import wwwpy.remote.component as wpc
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    btn2: js.HTMLButtonElement = wpc.element()
    """

    modified_source = add_property(original_source, 'MyElement',
                                   Attribute('btn2', 'js.HTMLButtonElement', 'wpc.element()'))

    assert modified_source == expected_source


def test_add_property__should_add_it_on_top_after_other_attributes():
    original_source = """
import wwwpy.remote.component as wpc
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    def foo(self):
        pass
    """

    expected_source = """import js

import wwwpy.remote.component as wpc
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    btn2: js.HTMLButtonElement = wpc.element()
    def foo(self):
        pass
    """

    modified_source = add_property(original_source, 'MyElement',
                                   Attribute('btn2', 'js.HTMLButtonElement', 'wpc.element()'))

    assert modified_source == expected_source


def test_add_property__should_honor_classname():
    original_source = """
class MyElement(wpc.Component):
        pass
class MyElement2(wpc.Component):
        pass
    """

    expected_source = """import js
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
        pass
class MyElement2(wpc.Component):
        btn1: js.HTMLButtonElement = wpc.element()
        pass
    """

    modified_source = add_property(original_source, 'MyElement2',
                                   Attribute('btn1', 'js.HTMLButtonElement', 'wpc.element()'))

    assert modified_source == expected_source


path01 = [0, 1]


def test_add_component():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

    expected_source = """import js

import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    btn1: js.Some = wpc.element()
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div>
<btn data-name="btn1"></btn></div>'''
    """

    component_def = ElementDef('btn', 'js.Some')
    add_result = add_component(original_source, 'MyElement', component_def, path01, Position.afterend)

    assert add_result.html == expected_source


def test_add_component_gen_html():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

    expected_source = """import js

import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    btn1: js.Some = wpc.element()
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div>
<btn data-name="btn1" attr1="bar"></btn></div>'''
    """

    def gen_html(element_def, data_name):
        return f'\n<btn data-name="{data_name}" attr1="bar"></btn>'

    component_def = ElementDef('btn', 'js.Some', gen_html=gen_html)
    add_result = add_component(original_source, 'MyElement', component_def, path01, Position.afterend)

    assert add_result.html == expected_source


def test_add_component_node_path__afterend():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

    def gen_html(element_def, data_name):
        return f'\n<btn data-name="{data_name}" attr1="bar"></btn>'

    component_def = ElementDef('btn', 'js.Some', gen_html=gen_html)
    add_result = add_component(original_source, 'MyElement', component_def, path01, Position.afterend)

    expected_node_path = [Node("div", 0, {'id': 'foo'}), Node('btn', 2, {'data-name': 'btn1', 'attr1': 'bar'})]
    assert add_result.node_path == expected_node_path


def test_add_component_node_path__beforebegin():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement(wpc.Component):
    def foo(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

    def gen_html(element_def, data_name):
        return f'\n<btn data-name="{data_name}" attr1="bar"></btn>'

    component_def = ElementDef('btn', 'js.Some', gen_html=gen_html)
    add_result = add_component(original_source, 'MyElement', component_def, path01, Position.beforebegin)

    expected_node_path = [Node("div", 0, {'id': 'foo'}), Node('btn', 1, {'data-name': 'btn1', 'attr1': 'bar'})]
    assert add_result.node_path == expected_node_path


def test_add_method():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement1(wpc.Component):
    btn1: js.Some = wpc.element()"""

    expected_source = original_source + """
    
    async def button1__click(self, event):
        pass
    """
    modified_source = add_method(original_source, 'MyElement1', 'button1__click', 'event')
    assert modified_source == expected_source


def test_add_method_custom_code():
    original_source = """
import wwwpy.remote.component as wpc
class MyElement1(wpc.Component):
    btn1: js.Some = wpc.element()"""

    expected_source = original_source + """
    
    async def button1__click(self, event):
        pass # custom
    """
    modified_source = add_method(original_source, 'MyElement1', 'button1__click', 'event', instructions='pass # custom')
    assert modified_source == expected_source


_default_imports = ['import wwwpy.remote.component as wpc', 'import js']


class TestEnsureImports:

    def assert_imports_ok(self, source):
        __tracebackhide__ = True

        def _remove_comment_if_present(line) -> str:
            line = line.strip()
            if '#' in line:
                line = line[:line.index('#')]
            return line.strip()

        modified_source = ensure_imports(source)
        modified_set = [_remove_comment_if_present(l) for l in ensure_imports(source).strip().split('\n')]
        # so it's order independent
        assert set(modified_set) == set(_default_imports)
        return modified_source

    def test_ensure_imports(self):
        self.assert_imports_ok('')

    def test_ensure_imports__should_not_duplicate_imports(self):
        self.assert_imports_ok('\n'.join(_default_imports))

    def test_ensure_imports__wpc_already_present(self):
        self.assert_imports_ok(_default_imports[0])

    def test_ensure_imports__js_already_present(self):
        self.assert_imports_ok(_default_imports[1])

    def test_ensure_imports__with_confounders(self):
        original_source = 'import js # noqa'
        modified_source = self.assert_imports_ok(original_source)
        assert original_source in modified_source
