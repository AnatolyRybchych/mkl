
from mklang.syntax import Syntax

import mklang.layout.tokenizer as tokenizer_layout
import mklang.layout.ast as ast_layout
import mklang.layout.settings as settings_layout

import mkc as c

class Layout:
    def __init__(self, syntax: Syntax):
        self.code = c.Codebase()
        self.dir = syntax.dir
        self.settings = settings_layout.Settings(syntax.settings)
        self.tokenizer = tokenizer_layout.Tokenizer(syntax.tokenizer)
        self.ast = ast_layout.Ast(syntax.ast, self.tokenizer.tokens)

    def generate(self) -> dict[str, str]:
        self.tokenizer.generate(self.code)
        self.ast.generate(self.code)

        return self.code.generate()

