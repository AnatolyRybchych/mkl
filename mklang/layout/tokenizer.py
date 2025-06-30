
import mklang.syntax.tokenizer as syntax
import mklang.layout.token as token_layout

import mkc as c
import json
import copy

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

# returns None if there is a cycle
def tree_depth(tree: dict) -> int | None:
    class Loop(Exception):
        pass

    def get_depth(tree: dict, visisted: set) -> int | None:
        res = 0
        visisted.add(id(tree))
        for k, v in tree.items():
            if id(v) in visisted:
                raise Loop
            res = max(res, get_depth(v, visisted))
        visisted.remove(id(tree))

        return res
    try:
        return get_depth(tree, set())
    except Loop:
        return None

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

        get_token = c_src.func(token_t, 'get_token', (cstring_t, 'beg'), (cstring_t, 'end'))
        body = get_token.body
        beg, end = body['beg'], body['end']

        cases: list[tuple[c.Expr, c.Construction]] = []

        for tok, steps in unique_token_steps.items():
            path = token_path(root, tok)

            if tree_depth(path) != 0:
                # TODO: handle multi-char tokens
                continue

            for step in steps:
                ret = c.Initializer(token_t, {
                    'type': token_type[self.tokens[tok].enum_name()],
                    'beg': beg,
                    'end': beg + 1,
                })

                cases.append((c.Literal(step, 'char'), c.Ret(ret)))

        body.add_switch(beg.deref(), cases)

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
