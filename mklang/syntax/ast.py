import xml.etree.ElementTree as ET

from mklang.syntax.ast_node import AstNode

class Ast:
    def __init__(self, **kw):
        self.nodes = {node['name']: AstNode(**node) for node in kw['nodes']}

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'ast'

        nodes = []

        for element in node:
            if element.tag == 'node':
                nodes.append(AstNode.parse_xml(element))
            else:
                raise Exception(f'Invalid xml node "{element.tag}" in ast')

        return {
            'nodes': nodes
        }
