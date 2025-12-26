#include <ast.h>
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
        case AST_FIELD:
            return sizeof(struct Ast_Field);
        case AST_STRUCT:
            return sizeof(struct Ast_Struct);
        default:
            return 0;
    }
}

AstNode* ast_node(Ast* ast, AstType type) {
    unsigned long node_size = get_node_size(type);
    unsigned long slot_size = sizeof(struct NodeBox) + node_size;
    struct NodeBox* res_slot = ast->allocator->alloc(ast->allocator, slot_size);
    if (!res_slot) {
        return (const AstNode*)(0);
    }
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
    if ((ctx->tokenizer.cur++)->type != TOK_NAME) {
        return (void*)(0);
    }
    return res;
}

const Ast_Field* parse_field(Ast* ast, ParserCtx* ctx) {
    Ast_Field* res = (Ast_Field*)(ast_node(ast, AST_FIELD));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    struct Ast_Type* node = parse_type(ast, ctx);
    if (!node) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_NAME) {
        return (void*)(0);
    }
    return res;
}

const Ast_Struct* parse_struct(Ast* ast, ParserCtx* ctx) {
    Ast_Struct* res = (Ast_Struct*)(ast_node(ast, AST_STRUCT));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if ((ctx->tokenizer.cur++)->type != TOK_STRUCT) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_NAME) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_OPEN_CURLY) {
        return (void*)(0);
    }
    struct Ast_Field* node = parse_field(ast, ctx);
    if (!node) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_CLOSE_CURLY) {
        return (void*)(0);
    }
    if ((ctx->tokenizer.cur++)->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    return res;
}
