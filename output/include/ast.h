#ifndef AST_H
#define AST_H

#include <token.h>
typedef enum {} AstType;

struct AstNode {
    union {
        AstType ast_type;
    };
};

#endif  // AST_H