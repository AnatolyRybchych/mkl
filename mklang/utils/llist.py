
from typing import Self

class LListNode:
    def __init__(self, value):
        self.value = value
        self.next = None
        self.has_next = False

    def add_next_node(self, node: Self) -> Self:
        assert not self.has_next
        assert type(node) is LListNode
        self.next = node
        self.has_next = True
        return self.next

    def add_next(self, value) -> Self:
        return self.add_next_node(LListNode(value))

    def iter_nodes(self):
        cur = self
        yield cur

        while cur.has_next:
            cur = cur.next
            yield cur

    def iter(self):
        for node in self.iter_nodes():
            yield node.value

    def is_cyclic(self) -> bool:
        visited: set = set()
        for node in self.iter_nodes():
            if node in visited:
                return True

            visited.add(node)

        return False

