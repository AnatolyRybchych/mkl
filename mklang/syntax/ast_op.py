import xml.etree.ElementTree as ET

class AstOp:
    def __init__(self, **kw):
        self.type = kw['type']
        self.field = kw.get('field', None)
        self.name = kw.get('name', None)
        self.items = kw.get('items', [])

    def parse_xml(node: ET.Element) -> dict:
        base = {
            'field': node.attrib.get('field'),
            'type': node.tag,
        }

        if node.tag == 'node':
            return {
                **base,
                'name': node.attrib['name'],
            }

        if node.tag == 'token':
            return {
                **base,
                'name': node.attrib['name']
            }

        raise Exception(f'Unexpected tag "{node.tag}" in ast node body')
