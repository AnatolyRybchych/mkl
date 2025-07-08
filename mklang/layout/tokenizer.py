
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

def string_match(node: fsm.Node) -> tuple[str, fsm.Node]:
    linear_path = fsm.get_linear_path(node).iter_break_cycles()

    string = ""
    for node in linear_path:
        keys = list(node.next.keys())
        if len(keys) != 1 or keys[0] == 0:
            return string, node

        if node.match:
            break

        string += str(bytes(keys), 'utf-8')

    return string, list(node.next_generation())[0]

class Tokenizer:
    def __init__(self, syntax: syntax.Tokenizer):
        self.tokens = {
            name: token_layout.Token(token_syntax) for name, token_syntax in syntax.tokens.items()
        }

    def generate_get_specific_token(self, src_file: c.File, func_name: str, tok_fsm: fsm.Node, token: token_layout.Token) -> c.Func:
        token_t = token_t = src_file.find_type('Token')
        get_specific_token = src_file.func(token_t, func_name, (c.char.const().ptr(), 'beg'), (c.char.const().ptr(), 'end'))
        body = get_specific_token.body
        beg, end = body['beg'], body['end']
        cur = body.declare(c.char.const().ptr(), 'cur', beg).var()
        get_token = body['token']
        token_type = src_file.find_type('TokenType')

        def return_node_token(node: fsm.Node, end) -> c.Ret:
            if node.match:
                return c.Ret(get_token(token_type[self.tokens[node.data].enum_name()], beg, cur))
            else:
                return c.Ret(get_token(token_type['TOK_EOF'], beg, end))

        cycles = fsm.get_cycle_roots(tok_fsm)
        nodes = fsm.get_all_nodes(tok_fsm)

        body_cur = body.add_logical_block()
        body_tail = body.add_logical_block()

        unresolved: list[tuple[fsm.Node, Block, Block, fsm.Node]] = [(tok_fsm, body_cur, body_tail, None)]

        while len(unresolved) != 0:
            fsm_node, block, block_tail, cycle_jmp = unresolved.pop()

            if fsm_node is cycle_jmp:
                continue

            next_branches = list(set([step for steps in fsm_node.next.values() for step in steps]))

            is_linear = len(next_branches) == 1
            if not is_linear:
                block.add_comment(f'TODO: handle non linear token {token.enum_name()}')
                block.add_line(c.Ret(get_token(token_type['TOK_EOF'], beg, cur)))
                continue

            next_branch = next_branches[0]

            conditions = [cur.deref() != c.Literal(key, 'char') for key in fsm_node.next.keys()]
            condition = cur == end
            for additional_condition in conditions:
                condition = c.Or(condition, additional_condition)

            if fsm_node in cycles:
                cycle_jmp = fsm_node
                while_loop = block.add_while(c.Not(condition))
                block.add_line(return_node_token(fsm_node, cur))
                block = while_loop.body.add_logical_block()
                block.add_line(cur.assign(cur + 1))
                block_tail = while_loop.body.add_logical_block()
            else:
                string, last_string_node = string_match(fsm_node)
                if len(string) > 1:
                    str_literal = c.Literal(string)
                    block.add_if(c.Or(
                        end - cur < len(string),
                        c.Fn('memcmp')(cur, str_literal, len(string))
                    ), c.Ret(get_token(token_type['TOK_EOF'], beg, cur)))
                    block.add_line(cur.assign(cur + len(string)))
                    next_branch = last_string_node
                else:
                    block.add_if(condition, return_node_token(fsm_node, cur))
                    block.add_line(cur.assign(cur + 1))

            if len(next_branch.next) == 0:
                block.add_line(return_node_token(next_branch, cur))
            else:
                unresolved.append((next_branch, block, block_tail, cycle_jmp))

        return get_specific_token

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
                get_cur_tok = self.generate_get_specific_token(c_src, f'{tok.lower()}_token', tok_fsm, self.tokens[tok])
                c_src.declare(get_cur_tok.func_decl())

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

        control_flow: fsm.Node = fsm.minimize(fsm.any(
            *[fsm.from_expr(tok.expr, tok.name) for tok in self.tokens.values()]
        ))

        self.generate_get_token(control_flow, token_c)
