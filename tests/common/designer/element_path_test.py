from tests.common import dyn_sys_path, DynSysPath
from tests.common.designer.component_fixture import ComponentFixture, component_fixture
from tests.common.designer.element_editor_test import _node_path
from wwwpy.common.designer import element_path
from wwwpy.common.designer.element_path import ElementPath
from wwwpy.common.designer.html_locator import html_to_node_path


def test_valid__path_to_component(component_fixture: ComponentFixture):
    html = """<button>bar</button>"""
    component_fixture.write_component('p1/comp1.py', 'Comp1', html=html)
    node_path = html_to_node_path(html, [0])
    target = ElementPath('p1.comp1', 'Comp1', node_path)
    assert target.valid()


def test_valid___path_to_component__not_valid_node_path(component_fixture: ComponentFixture):
    component_fixture.write_component('p1/comp1.py', 'Comp1', html="")
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = ElementPath('p1.comp1', 'Comp1', node_path)
    assert not target.valid()


def test_valid__class_do_not_exist(component_fixture: ComponentFixture):
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = ElementPath('p2.comp2', 'Comp2', node_path)
    assert not target.valid()


def test_valid__file_exists_but_class_do_not(component_fixture: ComponentFixture):
    component_fixture.write_component('p1/comp1.py', 'Comp1', html="")
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = ElementPath('p1.comp1', 'Comp2', node_path)
    assert not target.valid()
