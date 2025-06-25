import xml.etree.ElementTree as ET

from mklang.syntax.ast_op import AstOp

class AstNode:
    def __init__(self, **kw):
        self.name = kw['name']
        self.op = AstOp(**kw['op'])

        if self.op.type == 'seq':
            self.op.items = [AstOp(**item) for item in self.op.items]

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'node'

        ops = []
        for element in node:
            ops.append(AstOp.parse_xml(element))
        
        if len(ops) ==0 :
            ops = {'type': 'nop'}
        elif len(ops) == 1:
            ops = ops[0]
        else:
            ops = {'type': 'seq', 'items': ops}

        return {
            'name': node.attrib['name'],
            'op': ops
        }
