
import mklang.syntax.token as syntax

class Token:
    def __init__(self, syntax: syntax.Token):
        self.name: str = syntax.name
        self.expr: str | None = syntax.expr
        self.order: int | None = syntax.order

    def enum_name(self) -> str:
        return f'{self.name}'