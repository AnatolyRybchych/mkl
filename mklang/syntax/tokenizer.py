import xml.etree.ElementTree as ET

from mklang.syntax.token import Token

class Tokenizer:
    def __init__(self, **kw):
        self.tokens = {token['name']: Token(**token) for token in kw['tokens']}
        self.dump = [v.strip() for v in kw.get('dump', 'token_type').split(',')]

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'tokenizer'

        tokens = []

        for element in node:
            if element.tag == 'token':
                tokens.append(Token.parse_xml(element))
            else:
                raise Exception(f'Invalid xml node "{element.tag}" in tokenizer')

        attribs: set[str] = set([
            'dump'
        ])

        return {
            'tokens': tokens,
            **{k: v for k, v in node.attrib.items() if k in attribs}
        }
