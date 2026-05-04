#ifndef AST_H
#define AST_H

#include <token.h>
typedef enum {
    AST_TYPE,
    AST_FIELDS,
    AST_ARGS,
    AST_STRUCT,
    AST_FUNC_PROTO,
    AST_FUNC_DECL,
    AST_TOPLEVEL
} AstType;

typedef enum {
    PARSERE_OK,
    PARSERE_OUT_OF_MEMORY,
    PARSERE_UNEXPECTED_TOKEN
} ParserError;

typedef struct Ast_Type Ast_Type;
typedef struct Ast_Fields Ast_Fields;
typedef struct Ast_Args Ast_Args;
typedef struct Ast_Struct Ast_Struct;
typedef struct Ast_Func_proto Ast_Func_proto;
typedef struct Ast_Func_decl Ast_Func_decl;
typedef struct Ast_Toplevel Ast_Toplevel;
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

struct Ast_Func_proto {
    AstType ast_type;
    const Ast_Type* return_type;
    const struct Token* name;
    const Ast_Args* args;
};

struct Ast_Func_decl {
    AstType ast_type;
};

struct Ast_Toplevel {
    AstType ast_type;
    const AstNode* element;
    const Ast_Toplevel* next;
};

struct AstNode {
    union {
        AstType ast_type;
        Ast_Type node_type;
        Ast_Fields node_fields;
        Ast_Args node_args;
        Ast_Struct node_struct;
        Ast_Func_proto node_func_proto;
        Ast_Func_decl node_func_decl;
        Ast_Toplevel node_toplevel;
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
const Ast_Func_proto* parse_func_proto(Ast* ast, ParserCtx* ctx);
const Ast_Func_decl* parse_func_decl(Ast* ast, ParserCtx* ctx);
const Ast_Toplevel* parse_toplevel(Ast* ast, ParserCtx* ctx);

#endif  // AST_H