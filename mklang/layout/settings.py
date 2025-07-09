
import mklang.syntax.settings as syntax

class Settings:
    def __init__(self, syntax: syntax.Settings):
        self.defaults = {
            'output_header_dir.*': './output',
            'output_source_dir.*': './output',
        }

        self.parameters = syntax.parameters

    def __getitem__(self, key: str) -> str | None:
        cur = self.parameters
        for subscript in key.split('.'):
            if subscript in cur:
                cur = cur[subscript]
            else:
                return self.defaults.get(key)

        if type(cur) is dict:
            raise Exception(f'Incomplete setting path: {key}; expected {key}.{list[cur.keys()]}')

        return cur



    def enum_name(self) -> str:
        return f'TOK_{self.name}'