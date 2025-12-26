#ifndef AST_H
#define AST_H

#include <token.h>
typedef enum { AST_TYPE, AST_FIELD, AST_STRUCT } AstType;

typedef enum {
    PARSERE_OK,
    PARSERE_OUT_OF_MEMORY,
    PARSERE_UNEXPECTED_TOKEN
} ParserError;

typedef struct Ast_Type Ast_Type;
typedef struct Ast_Field Ast_Field;
typedef struct Ast_Struct Ast_Struct;
typedef struct AstNode AstNode;
typedef struct Allocator Allocator;
typedef struct ParserCtx ParserCtx;
typedef struct Ast Ast;
struct Ast_Type {
    AstType ast_type;
    struct Token* name;
};

struct Ast_Field {
    AstType ast_type;
    Ast_Type type;
    struct Token* name;
};

struct Ast_Struct {
    AstType ast_type;
    struct Token* name;
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

struct Allocator {
    void* (*alloc)(Allocator* self, unsigned long size);
    void (*free)(Allocator* self, void* ptr);
};

struct NodeBox {
    struct NodeBox* next;
    AstNode node[];
};

struct ParserCtx {
    AstNode* cur_node;
    struct {
        const struct Token* beg;
        const struct Token* cur;
        const struct Token* end;
    } tokenizer;
    ParserError error;
};

struct Ast {
    Allocator* allocator;
    const AstNode* root;
    struct NodeBox* nodes;
};

Ast* ast_init(Allocator* alloc);
void ast_clean(Ast* ast);
const Ast_Type* parse_type(Ast* ast, ParserCtx* ctx);
const Ast_Field* parse_field(Ast* ast, ParserCtx* ctx);
const Ast_Struct* parse_struct(Ast* ast, ParserCtx* ctx);

#endif  // AST_H