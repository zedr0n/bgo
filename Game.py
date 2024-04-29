from typing import List, Dict

class Item:
    def __init__(self) -> None:
        pass

    def bounding_box(self) -> tuple[int, int, int]:
        return 0,0,0
    
    def stacking_direction(self) -> str:
        return 'y'

class Card(Item):
    def __init__(self, length: int, width: int, thickness: int) -> None:
        self._length = length
        self._width = width
        self._thickness = thickness

    # in xyz
    def bounding_box(self) -> tuple[int, int, int]:
        return self._width, self._thickness, self._length
        

class ItemClass:
    def __init__(self, item: Item, count: int) -> None:
        self._item = item
        self._count = count
        pass

    def bounding_box(self, vertical: bool = True) -> tuple[int, int, int]:
        dim_x, dim_y, dim_z = self._item.bounding_box()
        if vertical:
            return dim_x, dim_y * self._count, dim_z
        else:
            return dim_z, dim_y * self._count, dim_x

class Game:
    def __init__(self, length: int, width: int, height: int) -> None:
        self.length = length
        self.width = width
        self.height = height
        self._items: Dict[Item, int] = {}

    def add_items(self, item: Item, count: int) -> None:
        if item in self._items:
            self._items[item] += count
        else:
            self._items[item] = count    
    
    def generate_classes(self) -> List[ItemClass]:
        classes: List[ItemClass] = []
        for i, c in self._items.items():
            classes.append(ItemClass(i, c))

        return classes
    
    def total_space(self, layers=1) -> List[int]:
        volume = self.length*self.width*self.height
        return [int(volume/layers) for v in range(layers)]

    def layer_size(self, layers=1) -> tuple[int, int, int]:
        return self.width, self.length, self.height

    def bounding_box(self):
        return self.width, self.length, self.height
