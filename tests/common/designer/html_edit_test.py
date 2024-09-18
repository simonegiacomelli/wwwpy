from wwwpy.common.designer.html_edit import html_add, Position, html_edit, html_attribute_set
from wwwpy.common.designer.html_locator import Node

# language=html
html = "<div id='foo'><div></div><div id='target'></div></div>"
path = [Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]


def test_add_beforebegin():
    actual = html_add(html, 'xyz', path, Position.beforebegin)
    # language=html
    assert actual == "<div id='foo'><div></div>xyz<div id='target'></div></div>"


def test_add_afterend():
    actual = html_add(html, 'xyz', path, Position.afterend)
    # language=html
    assert actual == "<div id='foo'><div></div><div id='target'></div>xyz</div>"


def test_edit():
    actual = html_edit(html, 'xyz', path)
    # language=html
    assert actual == "<div id='foo'><div></div>xyz</div>"


class TestAttributeSet:
    def test_attribute_set(self):
        actual = html_attribute_set(html, path, 'id', 'bar')
        # language=html
        assert actual == "<div id='foo'><div></div><div id='bar'></div></div>"

    def test_attribute_set_should_not_change_quote_char(self):
        # language=html
        html = """<div id="foo"><div></div><div id="target"></div></div>"""
        path = [Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]

        actual = html_attribute_set(html, path, 'id', 'bar')
        # language=html
        assert actual == """<div id="foo"><div></div><div id="bar"></div></div>"""

    def test_attribute_correct_escaping(self):
        actual = html_attribute_set(html, path, 'id', '<div1>')
        # language=html
        assert actual == "<div id='foo'><div></div><div id='&lt;div1&gt;'></div></div>"

    def test_attribute_set_None_value(self):
        path = [Node("button", 0, {'foo': '1'})]
        # language=html
        actual = html_attribute_set("<some foo='1'></some>", path, 'foo', None)
        # language=html
        assert actual == "<some foo></some>"

    def test_from_None_attribute_to_valued(self):
        path = [Node("some", 0, {'foo': None})]
        # language=html
        actual = html_attribute_set("<some foo></some>", path, 'foo', '123')
        # language=html
        assert actual == '<some foo="123"></some>'

    def test_from_missing_to_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some></some>", path, 'foo', '123')
        # language=html
        assert actual == '<some foo="123"></some>'

    def test_from_missing_to_None_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some></some>", path, 'foo', None)
        # language=html
        assert actual == '<some foo></some>'

    def test_pre_existing_add_None_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some bar='yes'></some>", path, 'foo', None)
        # language=html
        assert actual == "<some bar='yes' foo></some>"

    def test_pre_existing_add_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some bar='yes'></some>", path, 'foo', 'xyz')
        # language=html
        assert actual == """<some bar='yes' foo="xyz"></some>"""
