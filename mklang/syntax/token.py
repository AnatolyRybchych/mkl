import xml.etree.ElementTree as ET

class Token:
    def __init__(self, **kw):
        self.name = kw['name']
        self.expr = kw.get('expr')

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'token'
        assert node.attrib['name']

        return {
            'name': node.attrib['name'],
            'expr': node.text
        }
