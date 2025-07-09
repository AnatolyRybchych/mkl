import xml.etree.ElementTree as ET
import copy

class Settings:
    def __init__(self, **kw):
        self.parameters = copy.deepcopy(kw)

    def parse_xml(node: ET.Element) -> dict:
        assert node.tag == 'settings'

        def get_parameters(node: ET.Element) -> dict:
            settings: dict = {}
            for item in node:
                if item.tag in settings:
                    raise Exception(f'Duplicate tag "{node.tag}" in {node.tag} node body')

                params = {
                    '*': item.text.strip(),
                    **{f'#{key}': value for key, value in item.attrib.items()},
                    **{sub.tag: get_parameters(sub) for sub in item}
                }

                settings[item.tag] = params

            return settings

        return get_parameters(node)
