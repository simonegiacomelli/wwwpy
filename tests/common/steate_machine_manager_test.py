from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue
from typing import Any, Callable, Dict

import pytest

from enum import Enum
import pytest

class State(Enum):
    OPEN = 1
    LOADED = 2
    THROTTLE = 3

class StateMachine:
    def __init__(self):
        self.state = State.OPEN

    def event(self) -> bool:
        if self.state == State.OPEN:
            self.state = State.THROTTLE
            return True
        elif self.state == State.THROTTLE:
            self.state = State.LOADED
            return False
        elif self.state == State.LOADED:
            return False

    def timeout(self) -> bool:
        if self.state == State.THROTTLE:
            self.state = State.OPEN
            return False
        elif self.state == State.LOADED:
            self.state = State.OPEN
            return True

@pytest.fixture
def state_machine():
    return StateMachine()

def test_initial_state_transition(state_machine):
    assert state_machine.state == State.OPEN
    result = state_machine.event()
    assert state_machine.state == State.THROTTLE
    assert result is True

def test_throttling_state_transition(state_machine):
    state_machine.state = State.THROTTLE
    result = state_machine.event()
    assert state_machine.state == State.LOADED
    assert result is False

def test_timeout_in_throttling_state(state_machine):
    state_machine.state = State.THROTTLE
    result = state_machine.timeout()
    assert state_machine.state == State.OPEN
    assert result is False

def test_timeout_in_loaded_state(state_machine):
    state_machine.state = State.LOADED
    result = state_machine.timeout()
    assert state_machine.state == State.OPEN
    assert result is True

def test_event_in_loaded_state(state_machine):
    state_machine.state = State.LOADED
    result = state_machine.event()
    assert state_machine.state == State.LOADED
    assert result is False


@dataclass(order=True)
class Event:
    key: Any = field()
    item: Any = field(compare=False)  # example a change event 'modify', 'delete' etc.


@dataclass(order=True)
class _EventState:
    priority: datetime = field()
    event: Event = field(compare=False)
    state: StateMachine = field(compare=False, default=None)


class EventThrottler:
    def __init__(self, timeout_millis: int, emit: Callable[[Any], None], time_provider: Callable[[], datetime]):
        if time_provider is None:
            time_provider = datetime.utcnow
        self._time_provider = time_provider
        self._emit = emit
        self._timeout_millis = timeout_millis
        self._next: PriorityQueue[_EventState] = PriorityQueue()
        self._states: Dict[Any, _EventState] = {}

    def new_event(self, event: Event):
        prev_evt = self._states.get(event.key, None)
        if prev_evt is None:
            self._states[event.key] = _EventState(self._time_provider(), event)
            self._emit(event)
            return


def test_event_manager():
    items = []

    def callback(item: Any):
        items.append(item)

    now = datetime(2021, 1, 1, 0, 0, 0, 0)

    def time_provider():
        nonlocal now
        return now

    em = EventThrottler(50, callback, time_provider)
    e1 = Event('a', 'create')
    em.new_event(e1)
    assert items == [e1]


def test_event_in_window_should_be_withold():
    items = []

    def callback(item: Any):
        items.append(item)

    now = datetime(2021, 1, 1, 0, 0, 0, 0)

    def time_provider():
        nonlocal now
        return now

    em = EventThrottler(50, callback, time_provider)

    e1 = Event('a', 'create')
    em.new_event(e1)
    items.clear()

    now = now + timedelta(milliseconds=40)
    e2 = Event('a', 'modify')
    em.new_event(e2)
    assert items == []