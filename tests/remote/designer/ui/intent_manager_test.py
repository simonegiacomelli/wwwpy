from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import cached_property

import js
import pytest
from pyodide.ffi import create_proxy

from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.common._raise_on_any import RaiseOnAny, roa_get_config
from wwwpy.common.injectorlib import inject, injector
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.designer.ui import palette
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.designer.ui.intent import Intent
from wwwpy.remote.designer.ui.intent_manager import IntentManager
from wwwpy.remote.designer.ui.palette import PaletteComponent
from wwwpy.remote.jslib import is_instance_of

logger = logging.getLogger(__name__)


async def test_no_selected_intent(intent_manager):
    assert intent_manager.current_selection is None


async def test_click_intent__should_be_selected(intent_manager, intent1):
    await rpctst_exec("page.locator('#intent1').click()")

    assert intent_manager.current_selection == intent1
    assert intent1.selected
    assert intent1.events == ['on_selected']


async def test_manual_selection(intent_manager, intent1):
    intent_manager.current_selection = intent1

    assert intent_manager.current_selection == intent1
    assert intent1.selected
    assert intent1.events == ['on_selected']


async def test_click_twice_intent__should_be_deselected(intent_manager, intent1):
    await rpctst_exec(["page.locator('#intent1').click()", "page.locator('#intent1').click()"])

    assert intent_manager.current_selection is None
    assert not intent1.selected
    assert intent1.events == ['on_selected', 'on_deselect']


async def test_selecting_different_intent__should_deselect_previous(intent_manager, intent1, intent2,
                                                                    all_intent_events):
    # GIVEN
    await rpctst_exec(["page.locator('#intent1').click()"])
    all_intent_events.clear()

    # WHEN
    await rpctst_exec(["page.locator('#intent2').click()"])

    # THEN
    assert intent_manager.current_selection == intent2
    assert not intent1.selected
    assert intent2.selected
    assert all_intent_events == ['intent1:on_deselect', 'intent2:on_selected']


async def test_should_put_elements_on_screen(intent1, intent2):
    assert intent1.element.isConnected is True
    assert intent2.element.isConnected is True


async def test_externally_select_different_intent(intent_manager, intent1, intent2):
    # pytest.fail(f'innerHTML: `{js.document.body.innerHTML}`')
    # js.document.body.innerHTML =  '<button id="intent1">hello</button>'
    await rpctst_exec("page.locator('#intent1').click()")
    intent_manager.current_selection = intent2

    assert intent_manager.current_selection == intent2
    assert not intent1.selected
    assert intent2.selected


class TestUseSelection:
    async def test_selection_and_click__submitFalse_should_not_deselect(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = False
        intent_manager.current_selection = intent1

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(intent1.submit_calls) == 1
        assert intent_manager.current_selection is intent1
        assert div1.click_count == 1, 'div1 should have been clicked'

    async def test_selection_and_click__submitTrue_should_deselect(self, intent_manager, intent1, div1):
        # GIVEN
        intent_manager.current_selection = intent1
        intent1.submit_result = True

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(intent1.submit_calls) == 1
        assert intent_manager.current_selection is None
        assert div1.click_count == 0


class TestDrag:
    # see Playwright cancel drag here https://github.com/danielwiehl/playwright-bug-reproducer-dnd-cancel/blob/master/tests/reproducer.spec.ts
    # and generally https://chatgpt.com/share/67efcda6-9890-8006-8542-3634aa9249bf

    async def test_selected_drag__submitTrue_should_deselect(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = True
        intent_manager.current_selection = intent1

        # WHEN
        await rpctst_exec("page.locator('#intent1').drag_to(page.locator('#div1'))")

        # THEN
        assert intent_manager.current_selection is None
        assert not intent1.selected
        assert intent_manager.drag_state == DragFsm.IDLE

    async def test_no_select_start_drag__should_select_intent(self, intent_manager, intent1, div1):
        # GIVEN
        intent_manager.current_selection = None

        # WHEN
        await rpctst_exec(["page.locator('#intent1').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert intent_manager.current_selection is intent1
        assert intent_manager.drag_state == DragFsm.DRAGGING

    async def test_intent1_sel_and_start_drag_on_intent2__should_select_intent2(self, intent_manager, intent1, intent2,
                                                                                div1):
        # GIVEN
        intent_manager.current_selection = intent1

        # WHEN
        await rpctst_exec(["page.locator('#intent2').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert intent_manager.current_selection is intent2
        assert intent_manager.drag_state == DragFsm.DRAGGING

    async def test_change_selection_with_drag__should_select_intent2(self, intent_manager, intent1, intent2, div1):
        # GIVEN
        await rpctst_exec(["page.locator('#intent1').click()"])
        x, y = element_xy_center(div1)

        # WHEN
        await rpctst_exec(["page.locator('#intent2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert intent_manager.current_selection is intent2
        assert intent_manager.drag_state == DragFsm.DRAGGING

    async def test_no_selection_drag_and_drop__submitTrue_should_deselect(self, intent_manager, intent1, div1):
        # GIVEN
        intent_manager.current_selection = None
        intent1.submit_result = True  # could be more discriminating on 'div1'

        # WHEN
        await rpctst_exec("page.locator('#intent1').drag_to(page.locator('#div1'))")

        # THEN
        assert intent_manager.current_selection is None
        assert intent_manager.drag_state == DragFsm.IDLE

    async def test_no_selection_drag_and_drop(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = True

        # WHEN
        await rpctst_exec("page.locator('#intent1').drag_to(page.locator('#div1'))")

        # THEN
        assert intent_manager.current_selection is None

        assert intent1.events == ['on_selected', 'on_hover', 'on_execute', 'on_deselect']
        _, ev1, ev2, _ = intent1.full_events
        assert is_instance_of(ev1, js.PointerEvent), f'Expected js.PointerEvent, got {type(ev1)}'
        assert is_instance_of(ev2, js.PointerEvent), f'Expected js.PointerEvent, got {type(ev1)}'
        # assert is_instance_of(ev1, js.PointerEvent), f'ev1={ev1} type {type(ev1)}'
        # assert intent1.full_events[1].target == div1
        # assert intent1.full_events[2].target == div1
        # assert ev1.target == div1, f'ev1={ev1} type {type(ev1)}' # should be deep-target-of(ev1.target)
        # assert ev2.target == div1, f'ev2={ev2} type {type(ev2)}'

    async def test_no_select_not_enough_drag__should_not_select(self, intent_manager, intent1):
        # GIVEN
        x, y = element_xy_center(intent1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 3}, {y + 3})"])

        # THEN
        assert intent_manager.current_selection is None

    async def test_enough_drag__should_select(self, intent_manager, intent1):
        # GIVEN
        x, y = element_xy_center(intent1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 6}, {y + 6})"])

        # THEN
        assert intent_manager.current_selection is intent1
        assert intent1.events == ['on_selected']


class TestDragTouch:
    # TODO: implement touch drag tests
    async def todo_intent1_click_and_touch_drag_on_intent2__should_select_intent2(self, intent_manager, intent1,
                                                                                  intent2, div1):
        pass
        # look at `test_intent1_click_and_start_drag_on_intent2__should_select_intent2`
        # look at rpc4tests_test.py how to send touch events


class TestHover:

    async def test_selected_and_hover_on_intent__should_not_emit_Hover(self, intent_manager, intent1, intent2):
        # GIVEN
        intent_manager.current_selection = intent1

        # WHEN
        await rpctst_exec("page.locator('#intent2').hover()")

        # THEN
        assert intent_manager.current_selection is intent1  # should still be selected
        assert intent2.events == []

    async def test_selected_and_hover_on_div1__should_emit_Hover(self, intent_manager, intent1, div1):
        # GIVEN
        intent_manager.current_selection = intent1

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert intent_manager.current_selection is intent1  # should still be selected

        self._assert_intent_events_arrived_ok(intent1)

    async def test_drag_and_hover_on_div1__should_emit_Hover(self, intent_manager, intent1, div1):
        # GIVEN
        await rpctst_exec(["page.locator('#intent1').hover()", "page.mouse.down()"])
        logger.debug(f'drag state={intent_manager.drag_state}')
        # WHEN
        await rpctst_exec(["page.locator('#div1').hover()"])

        # THEN
        self._assert_intent_events_arrived_ok(intent1)

    def _assert_intent_events_arrived_ok(self, intent_fake: IntentFake):
        assert intent_fake.events != [], f'events not emitted innerHTML: `{js.document.body.innerHTML}`'


class TestStopEvents:
    @pytest.mark.parametrize("event_type", ['click', 'pointerdown', 'pointerup'])
    async def test_stop_event(self, intent_manager, intent1, event_type, div1):
        # GIVEN
        intent_manager.current_selection = intent1
        intent1.submit_result = True

        events = []
        div1.addEventListener(event_type, create_proxy(lambda ev: events.append(ev)))
        logger.debug(f'setup done')
        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert events == [], 'div1 event should not be fired'

    async def test_stop_event_should_not_stop_if_no_selection(self, intent_manager, div1):
        # GIVEN
        intent_manager.current_selection = None
        events = []
        div1.addEventListener('click', create_proxy(lambda ev: events.append(ev)))

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events) == 1, 'div1 event should be fired'


class TestEvents:
    def test_on_selected_programmatically(self, intent_manager, intent1):
        # WHEN
        intent_manager.current_selection = intent1

        # THEN
        assert intent1.events == ['on_selected']

    async def test_on_select__click(self, intent_manager, intent1):
        # WHEN
        await rpctst_exec("page.locator('#intent1').click()")

        # THEN
        assert intent1.events == ['on_selected']

    async def test_on_hover__hover(self, intent_manager, intent1, div1):
        # WHEN
        intent_manager.current_selection = intent1
        intent1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert intent1.events == ['on_hover']

    async def test_on_execute__drag(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = True

        # WHEN
        await rpctst_exec("page.locator('#intent1').drag_to(page.locator('#div1'))")

        # THEN
        assert intent1.events == ['on_selected', 'on_hover', 'on_execute', 'on_deselect']

    async def test_on_execute__click(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = True
        intent_manager.current_selection = intent1
        intent1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert intent1.events == ['on_hover', 'on_execute', 'on_deselect']

    async def test_on_execute__drag_submitFalse(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = False

        # WHEN
        await rpctst_exec("page.locator('#intent1').drag_to(page.locator('#div1'))")

        # THEN
        assert intent1.events == ['on_selected', 'on_hover', 'on_execute']
        assert div1.click_count == 0

    async def test_on_execute__click_submitFalse(self, intent_manager, intent1, div1):
        # GIVEN
        intent1.submit_result = False
        intent_manager.current_selection = intent1
        intent1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert intent1.events == ['on_hover', 'on_execute']
        assert div1.click_count == 1, 'div1 should have been clicked'

    async def test_change_selection_with_drag(self, intent1, intent2, div1, all_intent_events):
        # GIVEN
        await rpctst_exec(["page.locator('#intent1').click()"])
        x, y = element_xy_center(div1)
        all_intent_events.clear()

        # WHEN
        await rpctst_exec(["page.locator('#intent2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert all_intent_events == ['intent1:on_deselect', 'intent2:on_selected', 'intent2:on_hover', ]


@pytest.fixture
def intent_manager(fixture):
    yield fixture.intent_manager


@pytest.fixture
def intent1(fixture): yield fixture.intent1


@pytest.fixture
def intent2(fixture): yield fixture.intent2


@pytest.fixture
def div1(fixture): yield fixture.div1


@pytest.fixture
def all_intent_events(fixture):
    yield fixture.all_intent_events


@dataclass
class IntentFake(Intent):
    all_events: list = None
    events: list = field(default_factory=list)
    full_events: list[js.PointerEvent | str] = field(default_factory=list)
    submit_result = False
    submit_calls: list = field(default_factory=list)
    element: js.HTMLElement = None

    def _ev(self, kind, event: js.PointerEvent = None):
        self.events.append(kind)
        e = f'{self.label}:{kind}'
        self.all_events.append(e)
        self.full_events.append(event or kind)

    def on_selected(self):
        self._ev('on_selected')

    def on_hover_js(self, event: js.PointerEvent):
        if not is_instance_of(event, js.PointerEvent):
            raise TypeError(f'Expected js.PointerEvent, got {type(event)}')
        self._ev('on_hover', event)

    def on_submit_js(self, event: js.PointerEvent) -> bool:
        if not is_instance_of(event, js.PointerEvent):
            raise TypeError(f'Expected js.PointerEvent, got {type(event)}')
        self.submit_calls.append(event)
        self._ev('on_execute', event)
        return self.submit_result

    def on_deselected(self):
        self._ev('on_deselect')


@dataclass
class Fixture:
    intent_manager: IntentManager = inject()

    @cached_property
    def _palette(self):
        p = PaletteComponent()
        js.document.body.appendChild(p.element)
        return p

    def _add_intent(self, label: str) -> IntentFake:
        intent = IntentFake(label)
        intent.all_events = self.all_intent_events
        palette_item = self._palette.add_intent(intent)
        palette_item.element.id = label
        intent.element = palette_item.element
        return intent

    @cached_property
    def all_intent_events(self) -> list:
        return []

    @cached_property
    def intent1(self) -> IntentFake:
        return self._add_intent('intent1')

    @cached_property
    def intent2(self) -> IntentFake:
        return self._add_intent('intent2')

    @cached_property
    def div1(self) -> js.HTMLDivElement:
        div1 = js.document.createElement('div')
        div1.id = 'div1'
        div1.textContent = 'hello'
        div1.click_count = 0  # noqa monkeypatch
        div1.addEventListener('click', create_proxy(lambda ev: setattr(div1, 'click_count', div1.click_count + 1)))
        js.document.body.appendChild(div1)
        return div1


@pytest.fixture()
def fixture():
    f: Fixture
    try:
        injector._clear()
        palette.extension_point_register()
        am = IntentManager()
        injector.bind(am)
        f = Fixture()
        f.intent_manager.install()
    except Exception as e:
        logger.exception('RaiseOnAny!')
        raise_on_any = RaiseOnAny(f'RaiseOnAny=`{e}`')
        raise_config = roa_get_config(raise_on_any)
        raise_config.accept('intent_manager', 'palette', 'div1', 'intent1', 'intent2')
        f = raise_on_any  # noqa
    try:
        yield f
    finally:
        if not isinstance(f, RaiseOnAny):
            f.intent_manager.uninstall()
        palette.extension_point_unregister()
        injector._clear()
