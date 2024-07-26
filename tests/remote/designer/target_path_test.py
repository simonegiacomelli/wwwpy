import sys
from pathlib import Path
from time import sleep
from tests.common import restore_sys_path
from wwwpy.remote.designer.target_path import path_to_target, target_location, TargetLocation
from wwwpy.common.designer.html_locator import Node
from js import document, console


def test_target_path():
    div = document.createElement("div")
    div.innerHTML = """<div id='foo'><div></div><div id="target"></div></div>"""
    target = div.querySelector("#target")
    actual = path_to_target(target)
    expect = [Node("DIV", -1, {}), Node("DIV", 0, {'id': 'foo'}), Node("DIV", 1, {'id': 'target'})]
    console.log(f'actual={actual}')
    assert actual == expect, f'\nexpect={expect} \nactual={actual}'


def test_target_path_to_component(tmp_path, restore_sys_path):
    # GIVEN

    (tmp_path / 'component1.py').write_text('''import js

import wwwpy.remote.component as wpc


class Component1(wpc.Component):
    btn1: js.HTMLButtonElement = wpc.element()

    def connectedCallback(self):
        self.element.innerHTML = """
        <div></div>
        <div class='class1'>foo
            <button data-name='btn1' id='btn1id'>bar</button>
        </div>
    """
    ''')
    sys.path.insert(0, str(tmp_path))
    from component1 import Component1
    component1 = Component1()

    document.body.appendChild(component1.element)

    # WHEN
    target = document.querySelector("#btn1id")
    assert target
    actual = target_location(target)

    # THEN
    path = [Node("DIV", 1, {'class': 'class1'}),
            Node("BUTTON", 0, {'data-name': 'btn1', 'id': 'btn1id'})]

    expect = TargetLocation(component=component1, path=path)
    if str(actual) != str(expect):
        console.log(f'actual={actual}')
        console.log(f'expect={expect}')
        sleep(100)

    assert str(actual) == str(expect)


def disabled_test_html_locator__data_generator():
    """This is not a real test. Its purpose is to generate data
    that will be used for testing [html_locator]"""
    # div = document.createElement('div')
