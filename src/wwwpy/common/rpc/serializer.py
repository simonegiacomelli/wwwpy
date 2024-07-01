import json
from typing import NamedTuple, List, Tuple, Any, Optional, Dict, Callable, Awaitable, Iterable, Iterator

class RpcResponse(NamedTuple):
    result: Any
    exception: str

    @classmethod
    def from_json(cls, string: str) -> 'RpcResponse':
        obj = json.loads(string)
        response = RpcResponse(*obj)
        return response

    def to_json(self) -> str:
        return json.dumps(self, default=str)


class RpcRequest(NamedTuple):
    module: str
    func: str
    args: List[Optional[Any]]

    def json(self) -> str:
        return json.dumps(self)

    @classmethod
    def build_request(cls, module_name: str, func_name: str, *args) -> 'RpcRequest':
        return RpcRequest(module_name, func_name, args)

    @classmethod
    def from_json(cls, string: str) -> 'RpcRequest':
        obj = json.loads(string)
        request = RpcRequest(*obj)
        return request

