import copy
import json
import re
from typing import Any, Self, Generic, TypeVar
from mklang.utils.llist import LListNode

Key = TypeVar('Key')

class Node(Generic[Key]):
    def __init__(self, data = None) -> None:
        self.next: dict[Key, set[Node]] = {}
        self.data = data
        self.match = True

    def ref_child(self, key: Key, node: Self) -> None:
        if key not in self.next:
            self.next[key] = set()

        self.next[key].add(node)

    def next_generation(self) -> set[Self]:
        res: set[Node] = set()
        for steps in self.next.values():
            for step in steps:
                res.add(step)

        return res

def serializable(obj):
    if type(obj) == dict:
        return {k: serializable(v) for k, v in obj.items()}
    if type(obj) == list:
        return [serializable(v) for v in obj]
    if type(obj) == bytes:
        return str(obj, 'utf-8')
    return obj

def combine_sequentially(lhs: Node, rhs: Node) -> Node:
    rhs = copy.deepcopy(rhs)
    res = copy.deepcopy(lhs)

    visited: set[int] = set([res])
    unresolved = [res]

    while len(unresolved) != 0:
        cur = unresolved.pop()

        for step in cur.next.values():
            for node in step:
                if id(node) not in visited:
                    visited.add(id(node))
                    unresolved.append(node)

        # if cur.match and not cur.next:
        #     cur.match = rhs.match
        #     cur.next = rhs.next

        if cur.match:
            for key, steps in rhs.next.items():
                for node in steps:
                    cur.ref_child(key, node)
            cur.match = rhs.match

    return res

def combine_parallel(lhs: Node, rhs: Node) -> Node:
    rhs = copy.deepcopy(rhs)
    res = copy.deepcopy(lhs)

    visited: set[int] = set([res])
    unresolved = [(res, rhs)]

    while len(unresolved) != 0:
        cur_target, cur_source  = unresolved.pop()

        for key, src_step in cur_source.next.items():
            for src_node in src_step:
                cur_target.ref_child(key, src_node)

    return res

def seq(*nodes: Node) -> Node:
    to_combine = list(copy.deepcopy(node) for node in nodes)
    if len(to_combine) == 0:
        return Node()

    while len(to_combine) > 1:
        last = to_combine.pop()
        pre_last = to_combine.pop()
        to_combine.append(combine_sequentially(pre_last, last))

    return to_combine[0]

def any(*nodes: Node) -> Node:
    to_combine = list(copy.deepcopy(node) for node in nodes)
    if len(to_combine) == 0:
        return Node()

    while len(to_combine) > 1:
        last = to_combine.pop()
        pre_last = to_combine.pop()
        to_combine.append(combine_parallel(pre_last, last))

    return to_combine[0]

def expr_range_bytes(pattern: str|bytes) -> set[int]:
    if type(pattern) is str:
        pattern = bytes(pattern, 'utf-8')

    assert type(pattern) is bytes
    assert pattern[:1] == b'['
    assert pattern[-1:] == b']'

    pattern = pattern[1:-1]
    inverse = False
    if pattern[:1] == b'^':
        inverse = True
        pattern = pattern[1:]

    m = set()

    rng = pattern
    def shift(cnt = 1):
        nonlocal rng
        ret = rng[:1]
        rng = rng[1:]
        return ret

    def shift_unesc():
        val = shift()
        if val == b'\\':
            val = shift()
            if val == b'd': return expr_range_bytes(b'[0-9]'), val
            if val == b'D': return expr_range_bytes(b'[^0-9]'), val
            if val == b'w': return expr_range_bytes(b'[0-9a-zA-Z_]'), val
            if val == b'W': return expr_range_bytes(b'[^0-9a-zA-Z_]'), val
            if val == b's': return expr_range_bytes(b'[ \n\t\v\f\r]'), val
            if val == b'S': return expr_range_bytes(b'[^ \n\t\v\f\r]'), val
            return val, val
        else:
            return val, val

    lhs = b''
    while True:
        if not lhs:
            lhs, _ = lhs or shift_unesc()
        if not lhs:
            if inverse:
                return set(range(256)).difference(m)
            else:
                return m

        if type(lhs) is not bytes:
            m = set(list(m) + list(lhs))
            continue

        rhs = shift()
        if rhs == b'-':
            _, rhs = shift_unesc() or lhs
            m.update(list(range(min(lhs[0], rhs[0]), max(lhs[0], rhs[0]) + 1)))
            lhs = b''
        else:
            m.add(lhs[0])
            lhs = rhs

def from_expr_range(pattern: str | bytes, data) -> Node:
    bytes = expr_range_bytes(pattern)
    res = Node(data)
    res.match = False

    for b in bytes:
        res.ref_child(b, Node(data))

    return res

def from_utf8(text: str | bytes, data = None) -> Node:
    if type(text) is str:
        text = bytes(text, 'utf-8')
    
    assert type(text) is bytes

    node = Node(data)
    cur = node
    for b in text:
        new = Node(data)
        cur.match = False
        cur.next[b] = set([new])
        cur = new

    return node

def loop(node: Node):
    res = copy.deepcopy(node)

    visited: set[int] = set([res])
    unresolved = [res]

    while len(unresolved) != 0:
        cur = unresolved.pop()

        for steps in cur.next.values():
            for node in steps:
                if id(node) in visited:
                    continue

                if node.match:
                    if len(node.next) == 0:
                        steps.remove(node)
                        steps.add(res)
                        continue

                    node.next.update({k: copy.copy(beg_steps) for k, beg_steps in res.next.items()})

                visited.add(id(node))
                unresolved.append(node)

    res.match = True

    return res

def from_expr(pattern: str | bytes, data) -> Node:
    def unescape(str: bytes) -> bytes:
        res = b''
        while str != b'':
            ch, str = str[:1], str[1:]
            if ch != b'\\':
                res += ch
                continue

            ch, str = str[:1], str[1:]
            if ch == b'x':
                if not re.match(br'[0-9a-fA-F]{2}', str[:2]):
                    raise Exception(f'Not a valid hexadecimal value {str[:2]}')
                res += bytes([int(str[:2], base=16)])
                str = str[2:]
            elif ch == b'n':
                res += b'\n'
            elif ch == b't':
                res += b'\t'
            else:
                res += b'\\' + ch

        return res

    def tokenize(pattern: str | bytes) -> list[tuple[str, bytes]]:
        if type(pattern) is str:
            pattern = bytes(pattern, 'utf-8')

        assert type(pattern) is bytes
        pattern = unescape(pattern)

        res = []

        while pattern != b'':
            if pattern[0:1] == b'[':
                matched_rng = re.match(br'\[(?:[^\]]|\\])*\]', pattern)
                if not matched_rng:
                    raise Exception(f'Unmatched braces')

                rng = matched_rng.group()
                pattern = pattern[len(rng):]
                res.append(('RANGE', rng))
                continue

            if pattern[0:1] == b'(':
                matched_group = re.match(br'\((?:[^\(]|\))*\)', pattern)
                if not matched_group:
                    raise Exception(f'Unmatched parenthesis')

                group = matched_group.group()
                pattern = pattern[len(group):]
                res.append(('GROUP', group))
                continue

            if pattern[0:1] == b'*':
                res.append(('ARRAY', b'*'))
                pattern = pattern[1:]
                continue

            if pattern[0:1] == b'.':
                res.append(('WILDCARD', b'.'))
                pattern = pattern[1:]
                continue

            if pattern[0:1] == b'+':
                res.append(('NONEMPTY_ARRAY', b'+'))
                pattern = pattern[1:]
                continue

            if pattern[0:1] == b'?':
                res.append(('OPTIONAL', b'?'))
                pattern = pattern[1:]
                continue

            if pattern[0:1] == b'|':
                res.append(('OR', b'?'))
                pattern = pattern[1:]
                continue

            if pattern[0:1] == b'\\':
                res.append(('RANGE', b'['+pattern[:2]+b']'))
                pattern = pattern[2:]
                continue

            res.append(('TEXT', pattern[:1]))
            pattern = pattern[1:]

        return res

    def parse(tokens: list[tuple[str, str]]) -> list[dict]:
        branches = []
        cur = []
        for i, tok in enumerate(tokens):
            if tok[0] == 'OR':
                if len(cur) == 0: raise Exception(f'Missing target before "|" operator')
            else:
                cur.append(tok)

            if tok[0] == 'OR' or i == len(tokens) - 1:
                branches.append(cur)
                cur = []

        if len(branches) > 1:
            return [{'type': 'OR', 'or': [parse(toks) for toks in branches]}]

        res = []
        for tok, text in tokens:
            if tok == 'TEXT':
                if len(res) != 0 and res[-1]['type'] == 'TEXT':
                    res[-1]['text'] += text
                else:
                    res.append({'type': 'TEXT', 'text': text})
                continue

            if tok == 'RANGE':
                res.append({'type': "RANGE", 'range': text})
                continue

            if tok == 'WILDCARD':
                res.append({'type': "RANGE", 'range': b'[^\n]'})
                continue

            if tok == 'GROUP':
                res.append({'type': "GROUP", 'group': parse(tokenize(text[1:-1]))})
                continue

            if tok == 'ARRAY':
                if len(res) == 0:
                    raise Exception(f'Missing target before "*" operator')

                res[-1] = {'type': 'ARRAY', 'target': res[-1]}
                continue

            if tok == 'NONEMPTY_ARRAY':
                if len(res) == 0:
                    raise Exception(f'Missing target before "*" operator')

                res[-1] = {'type': 'NONEMPTY_ARRAY', 'target': res[-1]}
                continue

            if tok == 'OPTIONAL':
                if len(res) == 0:
                    raise Exception(f'Missing target before "?" operator')

                res[-1] = {'type': 'OPTIONAL', 'target': res[-1 ]}
                continue

            raise Exception(f'Not Implemented {tok}: {text}')

        return res

    def to_fsm(*exprs: dict) -> Node:
        res = []

        skip = 0
        for i, expr in enumerate(exprs):
            if skip != 0:
                skip -= 1
                continue

            if expr['type'] == 'OR':
                res.append(any(*[to_fsm(*branch) for branch in expr['or']]))
                continue
            
            if expr['type'] == 'GROUP':
                res.append(seq(to_fsm(*expr['group'])))
                continue

            if expr['type'] == 'RANGE':
                res.append(from_expr_range(expr['range'], data))
                continue

            if expr['type'] == 'TEXT':
                res.append(from_utf8(expr['text'], data))
                continue

            if expr['type'] in ['ARRAY', 'NONEMPTY_ARRAY'] :
                target = to_fsm(expr['target'])
                if expr['type'] == 'NONEMPTY_ARRAY':
                    res.append(copy.deepcopy(target))
                res.append(loop(target))
                continue

            raise Exception(f'Not Implemented: {json.dumps(serializable(expr))}')
        return seq(*res)

    return to_fsm(*parse(tokenize(pattern)))

def filter_fsm(predicate: callable, node: Node) -> Node:
    assert type(node) is Node

    res = copy.deepcopy(node)

    unresolved: set[Node] = set([res])
    visited: set[Node] = set()

    while len(unresolved) != 0:
        cur = unresolved.pop()
        if cur in visited:
            continue

        visited.add(cur)
        to_delete: set = set()

        for k in cur.next.keys():
            cur.next[k] = set(filter(predicate, cur.next[k]))

            for step in cur.next[k]:
                unresolved.add(step)

            if len(cur.next[k]) == 0:
                to_delete.add(k)

        for item in to_delete:
            del cur.next[item]

    return res

def get_cycle_roots(node: Node) -> set[Node]:
    res: set[Node] = set()
    unresolved: list[Node] = [node]
    visited: set[Node] = set()

    while len(unresolved) != 0:
        cur = unresolved.pop()
        if cur in visited:
            res.add(cur)
            continue
        visited.add(cur)

        for k, steps in cur.next.items():
            for step in steps:
                unresolved.append(step)

    return res

def get_all_nodes(node: Node) -> set[Node]:
    unresolved: list[Node] = [node]
    visited: set[Node] = set()

    while len(unresolved) != 0:
        cur = unresolved.pop()
        if cur in visited:
            continue

        visited.add(cur)

        for k, steps in cur.next.items():
            for step in steps:
                unresolved.append(step)

    return visited

def get_all_paths(node: Node) -> set[LListNode]:
    res: dict[tuple, LListNode] = {}

    def add_paths(bt: list[Node], visited: set[Node]):
        nonlocal res
        for steps in bt[-1].next.values():
            for step in steps:
                if len(step.next) == 0 and step.match or step in visited:
                    path = LListNode(bt[0])
                    cur = path
                    for path_step in [*bt[1:], step]:
                        cur = cur.add_next_node(LListNode(path_step))
                    res[tuple(path.iter_break_cycles())] = path
                    continue

                if id(step) in visited:
                    path = LListNode(bt[0])
                    cur = path
                    loop_root = None
                    for path_step in bt[1:]:
                        if path_step is step:
                            loop_root = step
                        cur = cur.add_next_node(LListNode(path_step))

                    cur = cur.add_next_node(LListNode(loop_root))
                    res[tuple(path.iter_break_cycles())] = path
                    continue

                visited.add(step)
                bt.append(step)
                add_paths(bt, visited)
                bt.pop()
                visited.remove(step)

    add_paths([node], set([node]))
    return set([value.next for value in res.values()])

def get_depth(node: Node) -> int:
    res = 0
    cur_gen: list[Node] = [node]
    next_gen: list[Node] = []
    visited: set[Node] = set()

    while len(cur_gen) != 0:
        while len(cur_gen) != 0:
            cur = cur_gen.pop()
            for steps in cur.next.values():
                for step in steps:
                    if step in visited:
                        continue
                    visited.add(step)
                    next_gen.append(step)

        cur_gen = next_gen
        next_gen = []
        res += 1

    return res

# returns dict[id(node), generation] where generation is distance to the edge
def get_node_generations(node: Node) -> dict[int, int]:
    res: dict[int, int] = {}

    def add_generations(node: Node, visited: set[Node]) -> int | None:
        nonlocal res

        if len(node.next) == 0:
            res[id(node)] = 0
            return 0

        if node in visited:
            return 0
        visited.add(node)

        generations = []
        cur_generation_steps: list[Node] = []
        for steps in node.next.values():
            for step in steps:
                generation = add_generations(step, visited) 
                generations += [generation + 1]
                cur_generation_steps.append(step)

        for step in cur_generation_steps:
            res[id(step)] = min(generations)

        return min(generations)

    add_generations(node, set())
    return res

# returns all the locations for each node dict[id(Node), tuple[parent node, key]]
def get_node_locations(node: Node) -> dict[int, list[tuple[Node, Any]]]:
    res: dict[int, list[tuple[Node, Any]]] = {}
    def add_location(parent: Node, key: Any, child: Node):
        nonlocal res
        assert child in parent.next[key]

        res[id(child)] = res.get(id(child), []) + [(parent, key)]

    visited: set[tuple[Node, Any, Node]] = set()
    unresolved: list[Node] = [node]

    while len(unresolved) != 0:
        cur = unresolved.pop()
        for key, steps in cur.next.items():
            for step in steps:
                location = (cur, key, step)
                if location in visited:
                    continue

                unresolved.append(step)
                visited.add(location)
                add_location(*location)

    return res

def minimize(root_node: Node) -> Node:
    res = copy.deepcopy(root_node)
    node_generations = get_node_generations(res)
    max_generation = max(node_generations.values())
    generations: list[list[Node]] = [[]] * (max_generation + 1)
    node_locations = get_node_locations(res)

    for node in get_all_nodes(res):
        if node is not res:
            generations[node_generations[id(node)]].append(node)

    def node_layout(node: Node) -> tuple:
        next = []
        for k, node_steps in node.next.items():
            steps = sorted([id(step) for step in node_steps])
            next.append((k, tuple(steps)))

        next = tuple(sorted(next, key=lambda tuple: tuple[0]))

        return (node.match, node.data, next)

    while len(generations) != 0:
        node_layouts: dict[tuple, list[Node]] = {}
        cur_generation = generations.pop()

        for node in cur_generation:
            layout = node_layout(node)
            node_layouts[layout] = node_layouts.get(layout, []) + [node]

        for duplicate_nodes in node_layouts.values():
            for node in duplicate_nodes[1:]:
                for location in node_locations[id(node)]:
                    parent, key = location
                    if node in parent.next[key]:
                        parent.next[key].remove(node)
                    parent.next[key].add(duplicate_nodes[0])

    return res

def get_linear_path(node: Node) -> LListNode:
    visited: dict[int, LListNode] = {}
    cur_node = node
    path: LListNode = LListNode(cur_node)
    cur = path

    while True:
        if id(cur_node) in visited:
            return cur.add_next_node(visited[id(cur_node)])

        visited[id(cur_node)] = cur

        branches = cur_node.next_generation()
        if len(branches) != 1:
            return path

        cur_node = branches.pop()
        cur = cur.add_next(cur_node)
