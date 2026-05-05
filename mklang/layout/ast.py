
import json

import mklang.syntax.ast as syntax
import mklang.syntax.ast_node as ast_node_syntax
import mklang.syntax.ast_op as ast_op_syntax
import mklang.layout.token as token_layout

import mklang.fsm as fsm

import mkc as c
import copy

from functools import cached_property

def dbg(block, msg):
    DEBUG: bool = True

    if not DEBUG:
        return

    block.add_comment(f'DBG: {msg}')

class AstOp:
    def __init__(self, type: str, syntax: ast_op_syntax.AstOp, **kw):
        self.type = type
        self.field = syntax.field
        self.node: AstNode = kw.get('node', None)
        self.token: token_layout.Token = kw.get('token', None)
        self.items: list[AstOp] = kw.get('items', [])
        self.aggregate_in: AstOp | None = None

        if self.type == 'any_of':
            for item in self.items:
                item.aggregate_in = self
                item.field = self.field

        if self.type == 'optional':
            field_items = [item for item in self.get_items_reqursively() if item.field]
            assert len(field_items) <= 1
            if field_items:
                self.field = field_items[0].field

    def get_items_reqursively(self) -> list[AstOp]:
        return self.items + [sub for item in self.items for sub in item.get_items_reqursively()]

    def make_fsm(self) -> fsm.Node:
        to_fsm = lambda x: x if type(x) is fsm.Node else x.make_fsm() if type(x) is AstOp else None

        if self.type == 'node':
            res = fsm.Node(None)
            res.match = False
            res.ref_child(('node', self.node.name), fsm.Node(self))
            return res

        if self.type == 'token':
            res = fsm.Node(None)
            res.match = False
            res.ref_child(('token', self.token.name), fsm.Node(self))
            return res

        if self.type == 'seq':
            to_combine: list = copy.copy(self.items)

            while len(to_combine) > 1:
                first = to_combine.pop(0)
                second = to_combine.pop(0)
                if type(second) is AstOp and second.type == 'optional':
                    assert type(first) is not AstOp or first.type != 'optional'
                    optional_second = fsm.seq(*[item.make_fsm() for item in second.items])
                    optional_second.match = True
                    to_combine.insert(0, fsm.combine_sequentially(to_fsm(first), optional_second))
                else:
                    to_combine.insert(0, fsm.combine_sequentially(to_fsm(first), to_fsm(second)))

            return to_fsm(to_combine[0])
        if self.type == 'any_of':
            return fsm.any(*[item.make_fsm() for item in self.items])

        raise Exception(f'make_fsm() is not implemented for the AstOp of type "{self.type}"')


class AstNode:
    def __init__(self, syntax: ast_node_syntax.AstNode, op: AstOp):
        self.name: str = syntax.name
        self.op: AstOp = op

    def struct_name(self) -> str:
        return f'Ast_{self.name.capitalize()}'

    def field_name(self) -> str:
        return f'node_{self.name.lower()}'

    def enum_name(self) -> str:
        return f'AST_{self.name}'

    def parse_node_name(self) -> str:
        return f'parse_{self.name.lower()}'

class Ast:
    def __init__(self, syntax: syntax.Ast, tokens: list[token_layout.Token]):
        self.nodes: dict[str, AstNode] = {}

        def mkop(syntax: ast_op_syntax.AstOp):
            nonlocal self
            nonlocal tokens

            if syntax.type == 'node':
                assert syntax.name in self.nodes
                return AstOp('node', syntax, node = self.nodes[syntax.name])
            elif syntax.type == 'token':
                assert syntax.name in tokens
                return AstOp('token', syntax, token = tokens[syntax.name])
            elif syntax.type == 'seq':
                return AstOp('seq', syntax, items = [mkop(item) for item in syntax.items])
            elif syntax.type == 'optional':
                return AstOp('optional', syntax, items = [mkop(item) for item in syntax.items])
            elif syntax.type == 'any_of':
                return AstOp('any_of', syntax, items = [mkop(item) for item in syntax.items])
            else:
                raise Exception(f'unexpected operation "{syntax.type}": {syntax}')

        for name, node in syntax.nodes.items():
            self.nodes[name] = AstNode(node, None)

        for name, node in syntax.nodes.items():
            self.nodes[name].op = mkop(node.op)

    def generate_parse_node(self, ast_c: c.File, node: AstNode) -> c.Func:
        cur_node_t = ast_c.find_type(node.struct_name()).typedef()
        token_t = ast_c.find_type('Token')
        token_type_t = ast_c.find_type('TokenType')
        ast_type_t = ast_c.find_type('AstType')
        parser_error_t = ast_c.find_type('ParserError')
        parser_ctx_t = ast_c.find_type('ParserCtx').typedef()
        ast_node_t = ast_c.find_type('AstNode').typedef()
        ast_t = ast_c.find_type('Ast').typedef()

        parse_node = ast_c.func(cur_node_t.const().ptr(), node.parse_node_name(),
            (ast_t.ptr(), 'ast'), (parser_ctx_t.ptr(), 'ctx'))

        body = parse_node.body
        ast, ctx = body['ast'], body['ctx']

        tokenizer_ctx = ctx.deref()['tokenizer']
        beg, cur, end = tokenizer_ctx['beg'], tokenizer_ctx['cur'], tokenizer_ctx['end']
        variables = body.add_logical_block()
        res = body.declare(cur_node_t.ptr(), 'res', c.Cast(cur_node_t.ptr(), c.Fn('ast_node')(ast, ast_type_t[node.enum_name()]))).var()
        if_node_init_failed = body.add_if(c.Not(res))
        if_node_init_failed.then.add_line(ctx.deref()['error'].assign(parser_error_t['OUT_OF_MEMORY']))
        if_node_init_failed.then.add_line(c.Ret(res))

        body.add_line(ctx.deref()['cur_node'].assign(c.Cast(ast_node_t.ptr(), res)))

        def check_step(node_type: str, node: AstOp, inverse: bool) -> c.Expr:
            if node_type == 'token':
                check = c.NotEquals if inverse else c.Equals
                return check(cur.deref()["type"], token_type_t[node])
            elif node_type == 'node':
                node_t: c.Type = variables.find_type(self.nodes[node].struct_name())
                node_var = variables.find_var(f'{node.lower()}_node') or variables.declare(node_t.const().ptr(), f'{node.lower()}_node', c.Literal(0)).var()
                node_found = node_var.assign(c.Fn(self.nodes[node].parse_node_name())(ast, ctx))
                return c.Not(node_found) if inverse else node_found
            else:
                assert False, f'Unexpected node: {(node_type, node)}'

        def on_step(block, ast_op: AstOp):
            if ast_op and ast_op.field:
                if ast_op.type == 'token':
                    block.add_line(res.deref()[ast_op.field].assign(c.PostInc(cur)))
                elif ast_op.type == 'node':
                    value = variables[f'{ast_op.node.name.lower()}_node']
                    if ast_op.aggregate_in and ast_op.aggregate_in.type == 'any_of':
                        value = c.Cast(ast_node_t.const().ptr(), value)
                    block.add_line(res.deref()[ast_op.field].assign(value))
                else:
                    assert False, f'Unexpected node type: {node_type}'
            elif ast_op.type == 'token':
                block.add_line(cur.assign(cur + 1))

        def branch(body, paths: fsm.Node):
            cycle_entries = fsm.get_cycle_roots(paths)
            cur_paths = paths

            while len(cur_paths.next) == 1:
                visited: set[fsm.Node] = set()

                expected_node = list(cur_paths.next.keys())[0]
                node_type, node = expected_node

                next_steps: set[AstNode] = cur_paths.next[expected_node]
                assert len(next_steps) == 1

                next_step: fsm.Node = list(next_steps)[0]
                ast_op: AstOp = next_step.data

                body.add_if(check_step(node_type, node, True),
                        c.Ret(res if cur_paths.match else c.Cast(c.void.ptr(), c.Literal(0))))

                on_step(body, ast_op)

                if next_step in visited:
                    break

                # TODO: handle some loops without recursion
                if next_step in cycle_entries:
                    visited.add(next_step)

                cur_paths = next_step

            if len(cur_paths.next) == 0:
                body.add_line(c.Ret(res))
                return

            token_branches = [branch for branch in cur_paths.next.keys() if branch[0] == 'token']
            node_branches = [branch for branch in cur_paths.next.keys() if branch[0] == 'node']
            other_branches = [branch for branch in cur_paths.next.keys() if branch[0] not in ['node', 'token']]
            assert len(other_branches) == 0, f'Not implemented for {other_branches}'

            cur_block = body
            for steps in token_branches + node_branches:
                next_steps = cur_paths.next[steps]
                assert len(next_steps) == 1, next_steps
                next_step: fsm.Node = list(next_steps)[0]

                node_type, node = steps
                if_statement = cur_block.add_if(check_step(node_type, node, False))

                ast_op: AstOp = next_step.data
                on_step(if_statement.then, ast_op)
                branch(if_statement.then, next_step)

                cur_block = c.construction.Block(cur_block)
                if_statement.otherwice = cur_block

            cur_block.add_line(c.Ret(res if cur_paths.match else c.Cast(c.void.ptr(), c.Literal(0))))
            body.add_line(c.Ret(res))

        branch(body, fsm.minimize(node.op.make_fsm()))
        return parse_node

    def generate(self, code: c.Codebase):
        ast_h = code.add_new_file('ast.h')
        ast_c = code.add_new_file('ast.c')
        ast_c.include_file(ast_h)
        ast_c.include_file('string.h')

        token_h = code.find_file('token.h')
        ast_h.include_file(token_h)
        ast_h.set_include_guard('AST_H')

        ast_type = ast_h.enum('AstType', *[node.enum_name() for node in self.nodes.values()])
        parser_error = ast_h.enum('ParserError', *['OK', 'OUT_OF_MEMORY', 'UNEXPECTED_TOKEN'])
        parser_error.type.set_prefix('PARSERE_')

        node_types = {}
        for node in self.nodes.values():
            node_type = ast_h.struct(node.struct_name(), ast_type = ast_type).typedef()
            node_types[node.struct_name()] = node_type
            ast_h.declare(node_type)

        ast_node_struct = ast_h.struct('AstNode')
        ast_node_t = ast_node_struct.typedef()
        ast_h.declare(ast_node_t)

        def node_field_type(op: AstOp) -> c.Type:
            if op.type == 'token':
                return ast_h.find_type('Token').const().ptr()
            elif op.type == 'node':
                return node_types[op.node.struct_name()].const().ptr()
            elif op.type == 'optional':
                field_items = [item for item in op.items if item.field]
                return node_field_type(field_items[0])
            elif op.type == 'any_of':
                return ast_node_t.const().ptr()
            else:
                raise Exception(f'Operation of type {op.type} is not supported')

        for node in self.nodes.values():
            node_struct = ast_h.find_type(node.struct_name())
            if node.op.type == 'seq':
                for item in node.op.items:
                    if item.field:
                        node_struct.add_field(node_field_type(item), item.field)
            elif node.op.field:
                node_struct.add_field(node_field_type(node.op), node.op.field)

        ast_node_union = c.Union('', ast_h)
        ast_node_union.add_field(ast_type, 'ast_type')
        for node in self.nodes.values():
            ast_node_union.add_field(node_types[node.struct_name()], node.field_name())

        ast_node_struct.add_field(ast_node_union, '')

        token_t = ast_h.find_type('Token')

        allocator_struct = ast_h.struct('Allocator')
        allocator_t = allocator_struct.typedef()
        ast_h.declare(allocator_t)
        alloc_fn_t = c.FuncType(c.void.ptr(), (allocator_t.ptr(), 'self'), (c.ulong, 'size'))
        free_fn_t = c.FuncType(c.void, (allocator_t.ptr(), 'self'), (c.void.ptr(), 'ptr'))
        allocator_struct.add_field(alloc_fn_t.ptr(), 'alloc')
        allocator_struct.add_field(free_fn_t.ptr(), 'free')

        node_slot_strcut = ast_h.struct('NodeBox')
        node_slot_strcut.add_field(node_slot_strcut.ptr(), 'next')
        node_slot_strcut.add_field(c.Array(ast_node_t), 'node')

        parser_ctx = ast_h.struct('ParserCtx')
        ast_h.declare(parser_ctx.typedef())
        parser_ctx.add_field(ast_node_t.ptr(), 'cur_node')

        tokenizer_struct = c.Struct('', parser_ctx)
        parser_ctx.add_field(tokenizer_struct, 'tokenizer')
        tokenizer_struct.add_field(token_t.const().ptr(), 'beg')
        tokenizer_struct.add_field(token_t.const().ptr(), 'cur')
        tokenizer_struct.add_field(token_t.const().ptr(), 'end')

        parser_ctx.add_field(parser_error, 'error')

        ast_struct = ast_h.struct('Ast')
        ast_t = ast_struct.typedef()
        ast_h.declare(ast_t)
        ast_struct.add_field(allocator_t.ptr(), 'allocator')
        ast_struct.add_field(ast_node_t.const().ptr(), 'root')
        ast_struct.add_field(node_slot_strcut.ptr(), 'nodes')

        def gen_ast_init(file: c.File):
            ast_init = file.func(ast_t.ptr(), 'ast_init', (allocator_t.ptr(), 'alloc'))

            body = ast_init.body
            alloc = body['alloc']

            res_decl = body.declare(ast_t.ptr(), 'res')
            res = res_decl.var()
            res_decl.expr = alloc.deref()['alloc'](alloc, c.SizeOf(res.deref()))

            body.add_if(c.Not(res), c.Ret(c.Cast(ast_t.ptr(), c.Literal(0))))
            body.add_line(res.deref().assign(c.Initializer(ast_t, {
                'allocator': alloc
            })))

            body.add_line(c.Ret(res))

            return ast_init

        ast_h.declare(gen_ast_init(ast_c).func_decl())

        def gen_ast_clean(file: c.File):
            ast_clean = file.func(c.void, 'ast_clean', (ast_t.ptr(), 'ast'))

            body = ast_clean.body
            ast = body['ast']

            body.add_if(c.Not(ast), c.Ret())

            cur_decl = c.DeclVar(node_slot_strcut.ptr(), 'cur', ast.deref()['nodes'])
            cur = cur_decl.var()

            nodes_free_loop = body.add_for(cur_decl, cur, c.Nop())
            to_free = nodes_free_loop.body.declare(node_slot_strcut.ptr(), 'to_free', cur).var()
            nodes_free_loop.body.add_line(cur.assign(cur.deref()['next']))
            nodes_free_loop.body.add_line(ast.deref()['allocator'].deref()['free'](ast.deref()['allocator'], to_free))

            body.add_line(ast.deref()['allocator'].deref()['free'](ast.deref()['allocator'], ast))

            return ast_clean

        ast_h.declare(gen_ast_clean(ast_c).func_decl())

        def gen_get_node_size(file: c.File):
            get_node_size = file.func(c.ulong, 'get_node_size', (ast_type, 'type'))

            body = get_node_size.body
            type = body['type']

            switch = body.add_switch(type)
            for node in self.nodes.values():
                switch.add_case(ast_type[node.enum_name()], c.Ret(c.SizeOfType(body.find_type(node.struct_name()))))
            switch.set_default(c.Ret(c.Literal(0)))

            return get_node_size

        ast_c.declare(gen_get_node_size(ast_c).func_decl())

        def gen_ast_node(file: c.File):
            ast_node = file.func(ast_node_t.ptr(), 'ast_node', (ast_t.ptr(), 'ast'), (ast_type, 'type'))

            body = ast_node.body
            type = body['type']
            ast = body['ast']
            node_size = body.declare(c.ulong, 'node_size', c.Fn('get_node_size')(type)).var()
            slot_size = body.declare(c.ulong, 'slot_size', c.SizeOfType(node_slot_strcut) + node_size).var()
            allocator = ast.deref()['allocator']

            res_slot = body.declare(node_slot_strcut.ptr(), 'res_slot', allocator.deref()['alloc'](allocator, slot_size)).var()
            body.add_if(c.Not(res_slot), c.Ret(c.Cast(ast_node_t.ptr(), c.Literal(0))))

            body.add_line(c.Fn('memset')(res_slot, 0, slot_size))

            body.add_line(res_slot.deref()['node'].deref()['ast_type'].assign(type))
            body.add_line(res_slot.deref()['next'].assign(ast.deref()['nodes']))
            body.add_line(ast.deref()['nodes'].assign(res_slot))

            # body.add_if(c.Not(ast.deref()['root']), ast.deref()['root'].assign(res_slot.deref()['node']))
            body.add_line(c.Ret(res_slot.deref()['node']))

            return ast_node

        ast_c.declare(gen_ast_node(ast_c).func_decl())

        for node in self.nodes.values():
            parse_node = self.generate_parse_node(ast_c, node)
            ast_h.declare(parse_node.func_decl())
