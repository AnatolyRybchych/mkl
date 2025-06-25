
import mklang.syntax.token as syntax

class Token:
    def __init__(self, syntax: syntax.Token):
        self.name = syntax.name
        self.expr = syntax.expr

    def enum_name(self) -> str:
        return f'TOK_{self.name}'