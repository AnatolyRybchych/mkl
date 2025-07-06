
import mklang.syntax.tokenizer as syntax
import mklang.layout.token as token_layout
import mklang.utils.tree as tree

import mkc as c
from mkc.consturction.block import Block

import json
import copy
import sys

import mklang.fsm as fsm

def group_by_token(node: fsm.Node) -> dict[str, set[int]]:
    res: dict[token_layout.Token, set[int]] = {}
    for key, steps in node.next.items():
        for step in steps:
            if step.data not in res:
                res[step.data] = set()
            res[step.data].add(key)
    return res

def token_path(node: fsm.Node, token: str) -> dict[int, dict]:
    def get_token_path(node: fsm.Node, token: str, visited: dict[fsm.Node, dict]) -> dict[int, dict]:
        if node in visited:
            return visited[node]

        res: dict[int, dict | None] = {}
        visited[node] = res

        for k, steps in node.next.items():
            for step in steps:
                if step.data == token:
                    res[k] = get_token_path(step, token, copy.copy(visited))
                    break

        return res

    return get_token_path(node, token, {})

def token_overlappings(token_steps: dict[str, set[int]], token: str) -> set[str]:
    target_steps: set[int] = token_steps[token]
    res: set[str] = set()
    for cur_tok, steps in token_steps.items():
        if not cur_tok == token and target_steps.intersection(steps):
            res.add(cur_tok)
    return res

class Tokenizer:
    def __init__(self, syntax: syntax.Tokenizer):
        self.tokens = {
            name: token_layout.Token(token_syntax) for name, token_syntax in syntax.tokens.items()
        }

    def generate_get_token(self, root: fsm.Node, c_src: c.File):
        token_steps: dict[str, set[int]] = group_by_token(root)

        overlapping_token_steps = {token: steps for token, steps in token_steps.items() if token_overlappings(token_steps, token)}
        unique_token_steps = {token: steps for token, steps in token_steps.items() if not token_overlappings(token_steps, token)}

        token_t = c_src.find_type('Token')
        token_type = c_src.find_type('TokenType')
        cstring_t = c.char.const().ptr()

        token_ctor = c_src.func(token_t, 'token', (token_type, 'type'), (cstring_t, 'beg'), (cstring_t, 'end'))
        c_src.declare(token_ctor.func_decl())
        token_ctor.body.add_line(c.Ret(c.Initializer(token_t, {
            'type': token_ctor.body['type'],
            'beg': token_ctor.body['beg'],
            'end': token_ctor.body['end'],
        })))

        get_token = c_src.func(token_t, 'get_token', (cstring_t, 'beg'), (cstring_t, 'end'))
        body = get_token.body
        beg, end = body['beg'], body['end']

        body.add_if(beg == end, c.Ret(token_ctor(token_type['TOK_EOF'], beg, beg)))

        body.declare(cstring_t, 'tok_end', beg + 1)
        tok_end = body['tok_end']

        beg_switch = body.add_switch(beg.deref())

        for tok, steps in unique_token_steps.items():
            tok_fsm = fsm.filter_fsm(lambda node: node.data == tok, root)

            path = token_path(root, tok)
            path_depth = tree.depth(path)

            if path_depth == 1:
                ret = token_ctor(token_type[self.tokens[tok].enum_name()], beg, tok_end)

                for step in steps:
                    beg_switch.add_case(c.Literal(step, 'char'), c.Ret(ret))
            else:
                get_cur_tok = c_src.func(token_t, f'{tok.lower()}_token', (cstring_t, 'beg'), (cstring_t, 'end'))
                cur_tok_body = get_cur_tok.body
                beg_cur_tok, end_cur_tok = cur_tok_body['beg'], cur_tok_body['end']

                c_src.declare(get_cur_tok.func_decl())

                cycles = fsm.get_cycle_roots(tok_fsm)
                nodes = fsm.get_all_nodes(tok_fsm)
                if len(cycles) == 1:
                    get_cur_tok.body.add_comment(f'TODO: handle cyclic token {tok} ({len(cycles)} cycles, {len(nodes)} nodes)')
                elif len(cycles) != 0:
                    # TODO: the FSM tree is not optimal, it should be one cycle and two nodes for SPACE token
                    get_cur_tok.body.add_comment(f'TODO: handle complex cyclic token {tok} ({len(cycles)} cycles, {len(nodes)} nodes)')
                else:
                    get_cur_tok.body.add_comment(f'TODO: handle non-cyclic token {tok}')

                for step in steps:
                    beg_switch.add_case(c.Literal(step, 'char'), c.Ret(c.Fn(get_cur_tok.name)(beg, end)))

        for tok, steps in overlapping_token_steps.items():
            body.add_comment(f'TODO: handle overlapping token {tok}')

        body.add_comment('The get_token function is not meant to fail.')
        body.add_comment('Return EOF with len != 0 for unknown token')
        body.add_line(c.Ret(token_ctor(token_type['TOK_EOF'], beg, beg + 1)))

    def generate(self, code: c.Codebase):
        token_h = code.add_new_file('output/include/token.h')
        token_h.set_include_guard('TOKENIZER_H')

        token_c = code.add_new_file('output/src/token.c')
        token_c.include_file(token_h)

        token_type = token_h.enum(f'TokenType', 'TOK_EOF', *[tok.enum_name() for tok in self.tokens.values()])

        token = token_h.struct('Token',
            type = token_type,
            beg = c.char.const().ptr(),
            end = c.char.const().ptr()).typedef()
        token_h.declare(token)

        control_flow: fsm.Node = fsm.any(
            *[fsm.from_expr(tok.expr, tok.name) for tok in self.tokens.values()]
        )

        self.generate_get_token(control_flow, token_c)
