#!/usr/bin/env python3

import mklang.fsm as fsm
import sys
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

def fsm_lookup(root_node: fsm.Node, path: str) -> set[fsm.Node]:
    cur = set([root_node])

    for ch in path:
        key = ord(ch)

        selected = set()
        for node in cur:
            if key in node.next:
                selected.update(node.next[key])

        cur = selected

    return cur


def interractive_test(root_node: fsm.Node):
    cur_text = ''

    while True:
        nodes = fsm_lookup(root_node, cur_text)

        matches = list(filter(lambda node: node.match,  nodes))
        sys.stdout.write(f'text: {cur_text}\n')
        sys.stdout.write(f'matches: {list(set(map(lambda match: match.data, matches)))}\n')
        sys.stdout.write('next steps: ')

        next_steps: dict[int, set[fsm.Node]] = {}
        for node in nodes:
            for key, steps in node.next.items():
                if key not in next_steps:
                    next_steps[key] = set()

                next_steps[key].update(steps)


        sep = ''
        for key, steps in next_steps.items():
            sys.stdout.write(sep)
            sep = ', '

            matching_steps = list(filter(lambda s: s.match, steps))

            key_text = chr(key)
            if not key_text.isascii() or key_text.isspace() or not key_text.isprintable():
                key_text = hex(key)

            if len(matching_steps) == 0:
                sys.stdout.write(key_text)
            elif len(matching_steps) == 1:
                sys.stdout.write(f'{Fore.GREEN}{key_text}{Style.RESET_ALL}')
            else:
                sys.stdout.write(f'{Fore.YELLOW}{key_text}{Style.RESET_ALL}')

        print()

        query = input()
        if not query:
            continue

        cur_text += query

sys.setrecursionlimit(10000)

node =  fsm.any(
    fsm.from_expr('[a-zA-Z_][a-zA-Z0-9_]*', 'NAME'),
    fsm.from_expr('struct', 'STRUCT'),
    fsm.from_expr('{', 'OPEN_CURLY'),
    fsm.from_expr('}', 'CLOSE_CURLY'),
    fsm.from_expr('\\(', 'OPEN_PARENTHESIS'),
    fsm.from_expr('\\)', 'CLOSE_PARENTHESIS'),
    fsm.from_expr('"([^"]|\\\\")*"', 'STRING')
)

interractive_test(node)