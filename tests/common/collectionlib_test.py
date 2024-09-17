from dataclasses import dataclass

from wwwpy.common import collectionlib as cl


@dataclass
class Item:
    name: str
    color: str


class MyListMap(cl.ListMap[Item]):
    def _key(self, item: Item) -> str:
        return item.name


def test_add_item():
    # GIVEN
    target = MyListMap()

    # WHEN
    target.append(Item('apple', 'red'))

    # THEN
    assert len(target) == 1
    assert target.get('apple').color == 'red'


def test_items_in_constructor():
    # GIVEN
    target = MyListMap(Item('apple', 'red'), Item('banana', 'yellow'))

    # THEN
    assert len(target) == 2
    assert target.get('apple').color == 'red'
    assert target.get('banana').color == 'yellow'
