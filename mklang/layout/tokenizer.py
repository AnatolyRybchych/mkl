
import mklang.syntax.tokenizer as syntax
import mklang.layout.token as token_layout

import mkc as c
import json

import mklang.fsm as fsm

def group_by_token(node: fsm.Node) -> dict[token_layout.Token, set[int]]:
    res: dict[token_layout.Token, set[int]] = {}
    for key, steps in node.next.items():
        for step in steps:
            if step.data not in res:
                res[step.data] = set()
            res[step.data].add(key)
    return res

def token_overlappings(token_steps: dict[token_layout.Token, set[int]], token: token_layout.Token) -> set[token_layout.Token]:
    target_steps: set[int] = token_steps[token]
    res: set[token_layout.Token] = set()
    for cur_tok, steps in token_steps.items():
        if not cur_tok is token and target_steps.intersection(steps):
            res.add(cur_tok)
    return res

def generate_get_token(root: fsm.Node, c_src: c.File):
    token_steps: dict[token_layout.Token, set[int]] = group_by_token(root)

    overlapping_token_steps = {token: steps for token, steps in token_steps.items() if token_overlappings(token_steps, token)}
    unique_token_steps = {token: steps for token, steps in token_steps.items() if not token_overlappings(token_steps, token)}

    # assume that one "if" condition cant be ugly as the token ranges are usually not very fragmented
    is_ugly_switch = lambda cases: len(cases) > 3
    unique_token_steps_to_switch = {token: steps for token, steps in unique_token_steps.items() if not is_ugly_switch(steps)}
    unique_token_steps_to_if = {token: steps for token, steps in unique_token_steps.items() if is_ugly_switch(steps)}

    if len(unique_token_steps_to_switch) < 3:
        unique_token_steps_to_if.update(unique_token_steps_to_switch)
        unique_token_steps_to_switch = {}

    for token, steps in unique_token_steps_to_switch.items():
        print('unique token:', token.name)

    token_t = c_src.find_struct('Token')
    cstring_t = c.char.const().ptr()

    get_token = c_src.func(token_t, 'get_token', (cstring_t, 'beg'), (cstring_t, 'end'))
    beg, end = get_token.body['beg'], get_token.body['end']

    


class Tokenizer:
    def __init__(self, syntax: syntax.Tokenizer):
        self.tokens = {
            name: token_layout.Token(token_syntax) for name, token_syntax in syntax.tokens.items()
        }

    def generate(self, code: c.Codebase):
        token_h = code.add_new_file('output/include/token.h')
        token_h.set_include_guard('TOKENIZER_H')

        token_c = code.add_new_file('output/src/token.c')
        token_c.include_file(token_h)

        token_type = token_h.enum(f'TokenType', 'END_OF_FILE', *[tok.enum_name() for tok in self.tokens.values()])

        token = token_h.struct('Token',
            type = token_type,
            beg = c.char.const().ptr(),
            end = c.char.const().ptr()).typedef()
        token_h.declare(token)

        control_flow: fsm.Node = fsm.any(
            *[fsm.from_expr(tok.expr, tok) for tok in self.tokens.values()]
        )

        generate_get_token(control_flow, token_c)
