import random
from typing import NamedTuple


class Position(NamedTuple):
    x: int
    y: int

    def __str__(self):
        return f"Position x: {self.x}, y: {self.y}"


class Size(NamedTuple):
    width: int
    height: int

    def __str__(self):
        return f"Size width: {self.width}, height: {self.height}"


class Block(NamedTuple):
    start: Position
    size: Size

    def __str__(self):
        return f"Block start: {self.start}, size: {self.size}"

    def get_random_position(self):
        return Position(
            x=random.randint(self.start.x + 1, self.start.x + self.size.width - 1),
            y=random.randint(self.start.y + 1, self.start.y + self.size.height - 1),
        )

    def get_top_center_position(self):
        return Position(
            x=self.start.x + self.size.width // 2,
            y=self.start.y
        )
