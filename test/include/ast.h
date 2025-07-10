#ifndef AST_H
#define AST_H

#include <token.h>
typedef enum { AST_TYPE, AST_FIELD, AST_STRUCT } AstType;

typedef struct Ast_Type Ast_Type;
typedef struct Ast_Field Ast_Field;
typedef struct Ast_Struct Ast_Struct;
struct Ast_Type {
    AstType ast_type;
    struct Token *name;
};

struct Ast_Field {
    AstType ast_type;
    Ast_Type type;
    struct Token *name;
};

struct Ast_Struct {
    AstType ast_type;
    struct Token *name;
    Ast_Field fields;
};

struct AstNode {
    union {
        AstType ast_type;
        Ast_Type node_type;
        Ast_Field node_field;
        Ast_Struct node_struct;
    };
};

const struct Ast_Type *parse_type(const struct Token *beg,
                                  const struct Token *end);
const struct Ast_Field *parse_field(const struct Token *beg,
                                    const struct Token *end);
const struct Ast_Struct *parse_struct(const struct Token *beg,
                                      const struct Token *end);

#endif  // AST_H