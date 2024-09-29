from dataclasses import dataclass, field

from wwwpy.remote.designer.ui.searchable_combobox2 import SearchableComboBox, Option
from js import document, window, console
from pyodide.ffi import create_proxy

import pytest


@pytest.fixture()
def target():
    target = SearchableComboBox()
    document.body.innerHTML = ''
    document.body.append(target.element)
    return target


def test_text_value(target):
    # GIVEN
    assert 'foo123' not in target.root_element().innerHTML

    # WHEN
    target.text_value = 'foo123'

    # THEN
    assert 'foo123' == target.text_value


def test_find_by_placeholder(target):
    target.placeholder = 'search...'
    assert '' == target.text_value
    target._input_element().value = 'foo123'
    assert 'foo123' == target.text_value


def test_popup_activate(target):
    options_str = ['foo', 'bar', 'baz']
    target.option_popup.options = options_str

    popup = target.option_popup.root_element()

    element_state(popup).assert_not_visible()
    target.option_popup.show()
    element_state(popup).assert_visible()

    html = popup.innerHTML
    for o in options_str:
        assert o in html


def test_popup_activate__with_input_click(target):
    # GIVEN
    options_str = ['foo', 'bar', 'baz']
    target.option_popup.options = options_str

    popup = target.option_popup.root_element()

    # WHEN
    target._input_element().click()

    # THEN
    element_state(popup).assert_visible()


def test_option_label_should_not_affect_text_value(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']
    bar = target.option_popup.options[1]
    bar.label = 'bar label'

    # WHEN
    target.option_popup.show()
    bar.do_click()

    # THEN
    assert target.text_value == 'bar'


def test_option_label_should_be_shown(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']
    bar = target.option_popup.options[1]
    bar.label = 'bar label'

    # WHEN
    target.option_popup.show()

    # THEN
    assert 'bar label' in bar.root_element().innerHTML



def test_popup__click_option(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']

    # WHEN
    target._input_element().click()
    target.option_popup.options[1].root_element().click()

    # THEN
    assert target.text_value == 'bar'

    popup = target.option_popup.root_element()
    element_state(popup).assert_not_visible()


def test_search__input_click__should_focus_search(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']
    target.option_popup.search_placeholder = 'search options...'

    # WHEN
    target._input_element().click()

    # THEN
    search_element = target.root_element().activeElement
    assert search_element
    assert search_element.placeholder
    assert search_element.placeholder == 'search options...'
    element_state(search_element).assert_visible()


def test_search_text__should_honor_search(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']

    # WHEN
    target._input_element().click()
    target.option_popup.search_value = 'ba'

    # THEN
    foo, bar, baz = [element_state(o.root_element()) for o in target.option_popup.options]
    bar.assert_visible()
    bar.assert_visible()
    foo.assert_not_visible()

    assert [o.visible for o in target.option_popup.options] == [False, True, True]


def test_outside_click__should_close_popup(target):
    # GIVEN
    button = document.createElement('button')
    document.body.append(button)

    target.option_popup.options = ['foo', 'bar', 'baz']
    target._input_element().click()

    # WHEN
    button.click()

    # THEN
    popup = target.option_popup.root_element()
    element_state(popup).assert_not_visible()


def test_click_twice__should_close_popup(target):
    # GIVEN
    target.option_popup.options = ['foo', 'bar', 'baz']
    target._input_element().click()

    # WHEN
    target._input_element().click()

    # THEN
    element_state(target.option_popup.root_element()).assert_not_visible()


def test_custom_option(target):
    # GIVEN
    target.option_popup.options = ['custom option', 'foo', 'bar', 'baz']
    option = target.option_popup.options[0]

    target.text_value = '123'

    # WHEN
    on_selected = []
    option.actions.set_input_value = False
    option.on_selected = lambda: [on_selected.append(True)]

    option.do_click()

    # THEN
    assert target.text_value == '123'
    assert not target.option_popup.visible
    assert on_selected == [True]


def test_change_event(target):
    # GIVEN
    target.placeholder = 'search...'
    target.option_popup.options = ['foo', 'bar', 'baz']

    # WHEN
    on_change = []
    target.element.addEventListener('wp-change', create_proxy(lambda e: [on_change.append(e.detail.option)]))
    target._input_element().click()
    bar = target.option_popup.options[1]
    bar.do_click()

    # THEN
    assert on_change == [bar]


def test_when_no_options__should_not_show_popup(target):
    # GIVEN

    # WHEN
    target._input_element().click()

    # THEN
    element_state(target.option_popup.root_element()).assert_not_visible()
    active_element = target.root_element().activeElement
    assert active_element == target._input_element()


@dataclass
class ElementState:
    document_contains: bool
    display: str
    visibility: str
    opacity: str
    width: float
    height: float
    visible: bool = field(init=False)

    def __post_init__(self):
        self.visible = (self.display != 'none' and self.visibility != 'hidden' and
                        self.opacity != '0' and self.width > 0 and self.height > 0)

    def assert_visible(self):
        __tracebackhide__ = True
        assert self.visible, self

    def assert_not_visible(self):
        __tracebackhide__ = True
        assert not self.visible, self


def element_state(element) -> ElementState:
    assert element
    e = element
    #  document.contains(element)
    style = window.getComputedStyle(e)
    rect = e.getBoundingClientRect()
    return ElementState(
        document_contains=document.contains(element),
        display=style.display,
        visibility=style.visibility,
        opacity=style.opacity,
        width=rect.width,
        height=rect.height,
    )
