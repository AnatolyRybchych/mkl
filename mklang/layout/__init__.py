
from mklang.syntax import Syntax

import mklang.layout.tokenizer as tokenizer_layout
import mklang.layout.ast as ast_layout

import mkc as c

class Layout:
    def __init__(self, syntax: Syntax):
        self.code = c.Codebase()
        self.tokenizer = tokenizer_layout.Tokenizer(syntax.tokenizer)
        self.ast = ast_layout.Ast(syntax.ast, self.tokenizer.tokens)

    def generate(self) -> dict[str, list[str]]:
        self.code.add_include_path("output/include")
        self.tokenizer.generate(self.code)
        self.ast.generate(self.code)
        self.code.generate()

