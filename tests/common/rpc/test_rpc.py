import importlib.util
from types import ModuleType

from tests.common.rpc import support1, support2
from wwwpy.rpc import Module, RpcRoute

support2_module_name = 'tests.common.rpc.support2'

support1_module_name = 'tests.common.rpc.support1'


# done migrating
def test_module_module():
    # WHEN
    target = Module(support1)

    # THEN
    assert target.name == 'tests.common.rpc.support1'
    assert len(target.functions) == 2


# done migrating
def test_module_function0():
    # WHEN
    target = Module(support1)

    # THEN
    fun = target.functions[0]
    assert fun.name == 'support1_function0'
    assert fun.signature == '(a: int, b: int) -> int'
    assert not fun.is_coroutine_function


# done migrating
def test_module_function1():
    # WHEN
    target = Module(support1)

    # THEN
    fun = target.functions[1]
    assert fun.name == 'support1_function1'
    assert fun.signature == '(a: int, b: float) -> str'
    assert fun.is_coroutine_function


# done migrating
def test_module_getitem_and_invoke():
    target = Module(support2)

    # THEN
    actual = target['support2_mul'].func(6, 7)
    assert actual == 42


def test_services_not_allowed():
    target = RpcRoute('/rpc1')
    actual = target.find_module(support2_module_name)
    assert actual is None

    target.add_module(support2_module_name)
    actual = target.find_module(support2_module_name)
    assert actual is not None
    actual: Module
    assert actual.name == support2_module_name


def test_module_that_do_not_exists():
    target = RpcRoute('/rpc1')
    target.add_module('missing_module.rpc')
    actual = target.find_module('missing_module.rpc')
    assert actual is None
