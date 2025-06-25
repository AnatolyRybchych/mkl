import xml.etree.ElementTree as ET

from mklang.syntax.ast import Ast
from mklang.syntax.tokenizer import Tokenizer

class Syntax:
    def __init__(self, **kw):
        ast = kw.get('ast', None)
        self.ast = ast and Ast(**ast)

        tokenizer = kw.get('tokenizer', None)
        self.tokenizer = ast and Tokenizer(**tokenizer)

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'layout'

        layout = {}

        for element in node:
            if element.tag == 'ast':
                assert 'ast' not in layout
                layout['ast'] = Ast.parse_xml(element)
            elif element.tag == 'tokenizer':
                assert 'tokenizer' not in layout
                layout['tokenizer'] = Tokenizer.parse_xml(element)
            else:
                raise Exception(f'Invalid xml node "{element.tag}" in layout')

        return layout
