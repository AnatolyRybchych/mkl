#ifndef AST_H
#define AST_H

#include <token.h>
typedef enum { AST_TYPE, AST_FIELDS, AST_ARGS, AST_STRUCT, AST_FDECL } AstType;

typedef enum {
    PARSERE_OK,
    PARSERE_OUT_OF_MEMORY,
    PARSERE_UNEXPECTED_TOKEN
} ParserError;

typedef struct Ast_Type Ast_Type;
typedef struct Ast_Fields Ast_Fields;
typedef struct Ast_Args Ast_Args;
typedef struct Ast_Struct Ast_Struct;
typedef struct Ast_Fdecl Ast_Fdecl;
typedef struct AstNode AstNode;
typedef struct Allocator Allocator;
typedef struct ParserCtx ParserCtx;
typedef struct Ast Ast;
struct Ast_Type {
    AstType ast_type;
    const struct Token* name;
};

struct Ast_Fields {
    AstType ast_type;
    const Ast_Type* type;
    const struct Token* name;
    const Ast_Fields* next;
};

struct Ast_Args {
    AstType ast_type;
    const Ast_Type* type;
    const struct Token* name;
    const Ast_Args* next;
};

struct Ast_Struct {
    AstType ast_type;
    const struct Token* name;
    const Ast_Fields* fields;
};

struct Ast_Fdecl {
    AstType ast_type;
    const Ast_Type* return_type;
    const struct Token* name;
    const Ast_Args* args;
};

struct AstNode {
    union {
        AstType ast_type;
        Ast_Type node_type;
        Ast_Fields node_fields;
        Ast_Args node_args;
        Ast_Struct node_struct;
        Ast_Fdecl node_fdecl;
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
const Ast_Fields* parse_fields(Ast* ast, ParserCtx* ctx);
const Ast_Args* parse_args(Ast* ast, ParserCtx* ctx);
const Ast_Struct* parse_struct(Ast* ast, ParserCtx* ctx);
const Ast_Fdecl* parse_fdecl(Ast* ast, ParserCtx* ctx);

#endif  // AST_H