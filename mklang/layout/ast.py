
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
            res = fsm.Node(self.name)
            res.match = False
            res.ref_child(('node', self.node.name), fsm.Node(self.name))
            return res

        if self.type == 'token':
            res = fsm.Node(self.name)
            res.match = False
            res.ref_child(('token', self.token.name), fsm.Node(self.name))
            return res

        if self.type == 'seq':
            return fsm.seq(*[item.make_fsm() for item, in self.items])

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
                return AstOp('token', syntax, node = tokens[syntax.name])
            elif syntax.type == 'seq':
                return AstOp('seq', syntax, items = [mkop(item) for item in syntax.items])
            else:
                raise Exception(f'unexpected operation "{syntax.type}": {json.dumps(syntax, indent=2)}')

        for name, node in syntax.nodes.items():
            self.nodes[name] = AstNode(node, mkop(node.op))

    def generate_parse_node(self, ast_c: c.File, node: AstNode) -> c.Func:
        node_type = ast_c.find_type(node.struct_name())
        token_t = ast_c.find_type('Token')

        parse_node = ast_c.func(node_type.const().ptr(), node.parse_node_name(),
            (token_t.const().ptr(), 'beg'), (token_t.const().ptr(), 'end'))

        return parse_node

    def generate(self, code: c.Codebase):
        ast_h = code.add_new_file('ast.h')
        ast_c = code.add_new_file('ast.c')
        ast_c.include_file(ast_h)

        token_h = code.find_file('token.h')
        ast_h.include_file(token_h)
        ast_h.set_include_guard('AST_H')

        ast_type = ast_h.enum('AstType', *[node.enum_name() for node in self.nodes.values()])

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
        ast_node_struct.add_field(ast_node_union, '')

        for node in self.nodes.values():
            parse_node = self.generate_parse_node(ast_c, node)
            ast_h.declare(parse_node.func_decl())

