import js
from pyodide.ffi import create_proxy

from wwwpy.common import quickstart
from wwwpy.remote import set_timeout
from wwwpy.remote.designer.ui.draggable_component import new_window, DraggableComponent
from wwwpy.remote.designer.ui.searchable_list_1 import SearchableList1, Item
from wwwpy.server.designer import rpc


class QuickstartUI:

    def __init__(self):
        self.window: DraggableComponent = new_window("Select a quickstart", closable=False).window
        # self.window.set_size('300px', '300px')
        self.window.set_position('5px', '5px')
        cmp1 = SearchableList1()
        cmp1.root_element().style.color = 'white'
        quickstart_list = quickstart.quickstart_list()
        self.quickstart_list = quickstart_list
        cmp1.items = [Item(qs.title, qs.description, {'quickstart': qs}) for qs in quickstart_list]
        cmp1.placeholder = 'Search or select below...'
        self.window.element.append(cmp1.element)

        cmp1.element.addEventListener('item-click', create_proxy(self._item_click_handler))

    def accept_quickstart(self, quickstart_name: str):
        self.window.element.remove()

        async def _notify_server():
            await rpc.quickstart_apply(quickstart_name)

        set_timeout(_notify_server)

    def _item_click_handler(self, event):
        item = event.detail
        assert isinstance(item, Item)
        self.accept_quickstart(item.values['quickstart'].name)


def create() -> QuickstartUI:
    return QuickstartUI()
