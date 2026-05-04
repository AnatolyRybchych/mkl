import xml.etree.ElementTree as ET

class AstOp:
    def __init__(self, **kw):
        self.type = kw['type']
        self.field = kw.get('field', None)
        self.name = kw.get('name', None)
        self.items: list[AstOp] = [AstOp(**item) for item in kw.get('items', [])]

        if self.type == 'any_of':
            assert all(item.field is None for item in self.get_items_reqursively()), \
                '"any_of" is an aggregator node - the fields should be references by the "any_of" node itself'

            assert all(item.type == 'node' for item in self.items), 'Only node aggregation is supported'

        if self.type == 'optional':
            assert not self.field, '"optional" cannot be a "field" - mark its element instead'
            assert len([item for item in self.get_items_reqursively() if item.field]) == 1, '"optional" can contain one "field" element'


    def get_items_reqursively(self) -> list[AstOp]:
        return self.items + [sub for item in self.items for sub in item.get_items_reqursively()]

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

        if node.tag == 'optional':
            return {
                **base,
                'items': [AstOp.parse_xml(item) for item in node]
            }

        if node.tag == 'any_of':
            return {
                **base,
                'items': [AstOp.parse_xml(item) for item in node]
            }