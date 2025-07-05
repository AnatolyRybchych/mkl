
from mklang.utils.llist import LListNode

import copy

# returns None if there is a cycle
def depth(tree: dict) -> int | None:
    class Loop(Exception):
        pass

    def get_depth(tree: dict, visisted: set) -> int | None:
        res = 0
        for k, v in tree.items():
            if id(v) in visisted:
                raise Loop
            visisted.add(id(v))
            res = max(res, get_depth(v, visisted) + 1)
            visisted.remove(id(v))

        return res
    try:
        return get_depth(tree, set([id(tree)]))
    except Loop:
        return None

def is_multibranch(tree: dict) -> bool:
    visited: set[dict] = set()
    cur = tree
    while True:
        if len(cur) > 1:
            return True
        elif len(cur) == 0:
            return False

        if cur in visited:
            return False

        cur = cur.values()[0]
        visited.add(cur)

def is_cyclic(tree: dict) -> bool:
    def get_is_cyclic(tree: dict, visited: set[dict]) -> bool:
        for v in tree.values():
            if v in visited:
                return True
            
            visited.add(v)
            if get_is_cyclic(tree, visited):
                return True
            visited.remove(v)
        return False

    return get_is_cyclic(tree, set())

