#include <ast.h>
#include <string.h>
unsigned long get_node_size(AstType type);
AstNode* ast_node(Ast* ast, AstType type);

Ast* ast_init(Allocator* alloc) {
    Ast* res = alloc->alloc(alloc, sizeof *res);
    if (!res) {
        return (Ast*)(0);
    }
    *res = (struct Ast){
        .allocator = alloc,
    };
    return res;
}

void ast_clean(Ast* ast) {
    if (!ast) {
        return;
    }
    for (struct NodeBox* cur = ast->nodes; cur;) {
        struct NodeBox* to_free = cur;
        cur = cur->next;
        ast->allocator->free(ast->allocator, to_free);
    }
    ast->allocator->free(ast->allocator, ast);
}

unsigned long get_node_size(AstType type) {
    switch (type) {
        case AST_TYPE:
            return sizeof(struct Ast_Type);
        case AST_FIELDS:
            return sizeof(struct Ast_Fields);
        case AST_ARGS:
            return sizeof(struct Ast_Args);
        case AST_STRUCT:
            return sizeof(struct Ast_Struct);
        case AST_FUNC_PROTO:
            return sizeof(struct Ast_Func_proto);
        case AST_FUNC_DECL:
            return sizeof(struct Ast_Func_decl);
        case AST_TOPLEVEL:
            return sizeof(struct Ast_Toplevel);
        default:
            return 0;
    }
}

AstNode* ast_node(Ast* ast, AstType type) {
    unsigned long node_size = get_node_size(type);
    unsigned long slot_size = sizeof(struct NodeBox) + node_size;
    struct NodeBox* res_slot = ast->allocator->alloc(ast->allocator, slot_size);
    if (!res_slot) {
        return (AstNode*)(0);
    }
    memset(res_slot, 0, slot_size);
    res_slot->node->ast_type = type;
    res_slot->next = ast->nodes;
    ast->nodes = res_slot;
    return res_slot->node;
}

const Ast_Type* parse_type(Ast* ast, ParserCtx* ctx) {
    Ast_Type* res = (Ast_Type*)(ast_node(ast, AST_TYPE));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    return res;
}

const Ast_Fields* parse_fields(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Type* type_node = 0;
    const struct Ast_Fields* fields_node = 0;
    Ast_Fields* res = (Ast_Fields*)(ast_node(ast, AST_FIELDS));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, ctx))) {
        return (void*)(0);
    }
    res->type = type_node;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(fields_node = parse_fields(ast, ctx))) {
        return res;
    }
    res->next = fields_node;
    return res;
}

const Ast_Args* parse_args(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Type* type_node = 0;
    const struct Ast_Args* args_node = 0;
    Ast_Args* res = (Ast_Args*)(ast_node(ast, AST_ARGS));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, ctx))) {
        return (void*)(0);
    }
    res->type = type_node;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_COMMA) {
        return res;
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(args_node = parse_args(ast, ctx))) {
        return (void*)(0);
    }
    res->next = args_node;
    return res;
}

const Ast_Struct* parse_struct(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Fields* fields_node = 0;
    Ast_Struct* res = (Ast_Struct*)(ast_node(ast, AST_STRUCT));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type != TOK_STRUCT) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_OPEN_CURLY) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(fields_node = parse_fields(ast, ctx))) {
        return (void*)(0);
    }
    res->fields = fields_node;
    if (ctx->tokenizer.cur->type != TOK_CLOSE_CURLY) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    return res;
}

const Ast_Func_proto* parse_func_proto(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Type* type_node = 0;
    const struct Ast_Args* args_node = 0;
    Ast_Func_proto* res = (Ast_Func_proto*)(ast_node(ast, AST_FUNC_PROTO));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, ctx))) {
        return (void*)(0);
    }
    res->return_type = type_node;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_OPEN_PARENTHESIS) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (ctx->tokenizer.cur->type == TOK_CLOSE_PARENTHESIS) {
        ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
        return res;
    } else if (args_node = parse_args(ast, ctx)) {
        res->args = args_node;
        if (ctx->tokenizer.cur->type != TOK_CLOSE_PARENTHESIS) {
            return (void*)(0);
        }
        ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
        return res;
    } else {
        return (void*)(0);
    }

    return res;
}

const Ast_Func_decl* parse_func_decl(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Func_proto* func_proto_node = 0;
    Ast_Func_decl* res = (Ast_Func_decl*)(ast_node(ast, AST_FUNC_DECL));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(func_proto_node = parse_func_proto(ast, ctx))) {
        return (void*)(0);
    }
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    return res;
}

const Ast_Toplevel* parse_toplevel(Ast* ast, ParserCtx* ctx) {
    const struct Ast_Struct* struct_node = 0;
    const struct Ast_Toplevel* toplevel_node = 0;
    const struct Ast_Func_decl* func_decl_node = 0;
    Ast_Toplevel* res = (Ast_Toplevel*)(ast_node(ast, AST_TOPLEVEL));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (struct_node = parse_struct(ast, ctx)) {
        res->element = (const AstNode*)(struct_node);
        if (!(toplevel_node = parse_toplevel(ast, ctx))) {
            return res;
        }
        res->next = toplevel_node;
        return res;
    } else if (func_decl_node = parse_func_decl(ast, ctx)) {
        res->element = (const AstNode*)(func_decl_node);
        if (!(toplevel_node = parse_toplevel(ast, ctx))) {
            return res;
        }
        res->next = toplevel_node;
        return res;
    } else {
        return (void*)(0);
    }

    return res;
}
