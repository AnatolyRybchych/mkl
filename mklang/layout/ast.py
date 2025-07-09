
import json

import mklang.syntax.ast as syntax
import mklang.syntax.ast_node as ast_node_syntax
import mklang.syntax.ast_op as ast_op_syntax
import mklang.layout.token as token_layout

import mkc as c

class AstOp:
    def __init__(self, type: str, syntax: ast_op_syntax.AstOp, **kw):
        self.type = type
        self.field = syntax.field
        self.node: AstNode = kw.get('node', None)
        self.token: token_layout.Token = kw.get('token', None)
        self.items: list[AstOp] = kw.get('items', [])

class AstNode:
    def __init__(self, syntax: ast_node_syntax.AstNode, op: AstOp):
        self.name: str = syntax.name
        self.op: AstOp = op

    def typename(self) -> str:
        return f'Ast_{self.name.capitalize()}'
    
    def fieldname(self) -> str:
        return f'node_{self.name.lower()}'

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

    def generate(self, code: c.Codebase):
        ast_h = code.add_new_file('ast.h')
        token_h = code.find_file('token.h')

        ast_h.set_include_guard('AST_H')
        ast_h.include_file(token_h)

        ast_type = ast_h.enum('AstType', *[f'AST_{node.name}' for node in self.nodes.values()])

        node_types = {}
        for node in self.nodes.values():
            node_type = ast_h.struct(node.typename(), ast_type = ast_type).typedef()
            node_types[node.typename()] = node_type
            ast_h.declare(node_type)

        def node_field_type(op: AstOp) -> c.Type:
            if op.type == 'token':
                return ast_h.find_type('Token').ptr()
            elif op.type == 'node':
                return node_types[op.node.typename()]
            else:
                raise Exception(f'Operation of type {op.type} is not supported')

        for node in self.nodes.values():
            node_struct = ast_h.find_type(node.typename())
            if node.op.type == 'seq':
                for item in node.op.items:
                    if item.field:
                        node_struct.add_field(node_field_type(item), item.field)
            elif node.op.field:
                node_struct.add_field(node_field_type(node.op), node.op.field)

        ast_node_union = c.Union('', ast_h)
        ast_node_union.add_field(ast_type, 'ast_type')
        for node in self.nodes.values():
            ast_node_union.add_field(node_types[node.typename()], node.fieldname())

        ast_node_struct = ast_h.struct('AstNode')
        ast_node_struct.add_field(ast_node_union, '')

