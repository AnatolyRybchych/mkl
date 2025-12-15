
import json

import mklang.syntax.ast as syntax
import mklang.syntax.ast_node as ast_node_syntax
import mklang.syntax.ast_op as ast_op_syntax
import mklang.layout.token as token_layout

import mklang.fsm as fsm

import mkc as c

class AstOp:
    def __init__(self, type: str, syntax: ast_op_syntax.AstOp, **kw):
        self.type = type
        self.field = syntax.field
        self.node: AstNode = kw.get('node', None)
        self.token: token_layout.Token = kw.get('token', None)
        self.items: list[AstOp] = kw.get('items', [])

    def make_fsm(self) -> fsm.Node:
        if self.type == 'node':
            res = fsm.Node(self.node.name)
            res.match = False
            res.ref_child(('node', self.node.name), fsm.Node(self.node.name))
            return res

        if self.type == 'token':
            res = fsm.Node(self.token.name)
            res.match = False
            res.ref_child(('token', self.token.name), fsm.Node(self.token.name))
            return res

        if self.type == 'seq':
            return fsm.seq(*[item.make_fsm() for item in self.items])

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
            else:
                raise Exception(f'unexpected operation "{syntax.type}": {json.dumps(syntax, indent=2)}')

        for name, node in syntax.nodes.items():
            self.nodes[name] = AstNode(node, mkop(node.op))

    def generate_parse_node(self, ast_c: c.File, node: AstNode) -> c.Func:
        cur_node_t = ast_c.find_type(node.struct_name())
        token_t = ast_c.find_type('Token')
        token_type_t = ast_c.find_type('TokenType')

        parse_node = ast_c.func(cur_node_t.const().ptr(), node.parse_node_name(),
            (token_t.const().ptr(), 'beg'), (token_t.const().ptr(), 'end'))

        body = parse_node.body
        beg, end = body.find_var('beg'), body.find_var('end')

        cur_tok: c.Var = body.declare(token_t.const().ptr(), 'cur_tok', beg).var()

        paths = node.op.make_fsm()
        cycle_entries = fsm.get_cycle_roots(paths)

        if cycle_entries:
            body.add_comment(f'TODO: handle cyclic structures {cycle_entries}')
            return parse_node
        
        cur_paths = paths
        while len(cur_paths.next) != 0:
            if len(cur_paths.next) != 1:
                body.add_comment('TODO: handle fancy if/switch dispatching')
                return parse_node

            expected_node = list(cur_paths.next.keys())[0]
            node_type, node = expected_node

            if node_type == 'token':
                body.add_if(c.NotEquals(c.PostInc(cur_tok).deref()["type"], token_type_t[node]),
                    c.Ret(c.Cast(c.void.ptr(), c.Literal(0))))
            elif node_type == 'node':
                node_t: c.Type = body.find_type(self.nodes[node].struct_name())
                node_found = body.declare(node_t.ptr(), 'node', c.Fn(self.nodes[node].parse_node_name())(cur_tok, end)).var()
                body.add_if(c.Not(node_found), c.Ret(c.Cast(c.void.ptr(), c.Literal(0))))
            else:
                assert False, f'Unexpected node type: {node_type}'



            next_steps: set[AstNode] = cur_paths.next[expected_node]
            if len(next_steps) != 1:
                body.add_comment('TODO: handle fancy if/switch dispatching')
                return parse_node

            next_step = list(next_steps)[0]
            cur_paths = next_step
        
        res_decl = body.declare(cur_node_t.ptr(), 'res')
        res = res_decl.var()
        res_decl.expr = c.Fn('malloc')(c.SizeOf(res.deref()))
        body.add_line(c.Fn('assert')(res))
        body.add_line(c.Assign(res.deref(), c.Initializer(cur_node_t, {})))
        body.add_line(c.Ret(res))

        return parse_node

    def generate(self, code: c.Codebase):
        ast_h = code.add_new_file('ast.h')
        ast_c = code.add_new_file('ast.c')
        ast_c.include_file(ast_h)

        token_h = code.find_file('token.h')
        ast_h.include_file(token_h)
        ast_h.set_include_guard('AST_H')

        ast_type = ast_h.enum('AstType', *[node.enum_name() for node in self.nodes.values()])
        parser_error = ast_h.enum('ParserError', *[f'PARSERE_{it}' for it in ['OK', 'OUT_OF_MEMORY', 'UNEXPECTED_TOKEN']])

        node_types = {}
        for node in self.nodes.values():
            node_type = ast_h.struct(node.struct_name(), ast_type = ast_type).typedef()
            node_types[node.struct_name()] = node_type
            ast_h.declare(node_type)

        def node_field_type(op: AstOp) -> c.Type:
            if op.type == 'token':
                return ast_h.find_type('Token').ptr()
            elif op.type == 'node':
                return node_types[op.node.struct_name()]
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

        ast_node_struct = ast_h.struct('AstNode')
        ast_node_t = ast_node_struct.typedef()
        ast_h.declare(ast_node_t)

        ast_node_struct.add_field(ast_node_union, '')

        for node in self.nodes.values():
            parse_node = self.generate_parse_node(ast_c, node)
            ast_h.declare(parse_node.func_decl())

        token_t = ast_h.find_type('Token')

        ast_struct = ast_h.struct('Ast')
        ast_t = ast_struct.typedef()
        ast_h.declare(ast_t)

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
        ast_struct.add_field(allocator_t.ptr(), 'allocator')
        ast_struct.add_field(ast_node_t.const().ptr(), 'root')
        ast_struct.add_field(node_slot_strcut.ptr(), 'nodes')

        parser_ctx = ast_h.struct('ParserCtx')
        parser_ctx.add_field(ast_node_t.ptr(), 'root_node')
        parser_ctx.add_field(ast_node_t.ptr(), 'cur_node')

        tokenizer_struct = c.Struct('', parser_ctx)
        parser_ctx.add_field(tokenizer_struct, 'tokenizer')
        tokenizer_struct.add_field(token_t.const().ptr(), 'beg')
        tokenizer_struct.add_field(token_t.const().ptr(), 'cur')
        tokenizer_struct.add_field(token_t.const().ptr(), 'end')
        
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
            nodes_free_loop.body.add_line(ast.deref()['allocator'].deref()['free'](to_free))

            body.add_line(ast.deref()['allocator'].deref()['free'](ast))

            return ast_clean

        ast_h.declare(gen_ast_clean(ast_c).func_decl())


