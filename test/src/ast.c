#include <ast.h>
#include <string.h>
unsigned long get_node_size(AstType type);
AstNode* ast_node(Ast* ast, AstType type);
struct ParserCtx* set_ctx(struct ParserCtx* dst, struct ParserCtx* src);

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
        case AST_EXPR_NUM:
            return sizeof(struct Ast_Expr_num);
        case AST_EXPR_ADD:
            return sizeof(struct Ast_Expr_add);
        case AST_EXPR_SUB:
            return sizeof(struct Ast_Expr_sub);
        case AST_EXPR_MUL:
            return sizeof(struct Ast_Expr_mul);
        case AST_EXPR_DIV:
            return sizeof(struct Ast_Expr_div);
        case AST_EXPR:
            return sizeof(struct Ast_Expr);
        case AST_CONSTR_RETURN:
            return sizeof(struct Ast_Constr_return);
        case AST_CONSTR:
            return sizeof(struct Ast_Constr);
        case AST_FUNC:
            return sizeof(struct Ast_Func);
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

struct ParserCtx* set_ctx(struct ParserCtx* dst, struct ParserCtx* src) {
    *dst = *src;
    return dst;
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
    ParserCtx tmp_ctx;
    const struct Ast_Type* type_node = 0;
    const struct Ast_Fields* fields_node = 0;
    Ast_Fields* res = (Ast_Fields*)(ast_node(ast, AST_FIELDS));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->type = type_node;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(fields_node = parse_fields(ast, set_ctx(&tmp_ctx, ctx)))) {
        return res;
    }
    set_ctx(ctx, &tmp_ctx);
    res->next = fields_node;
    return res;
}

const Ast_Args* parse_args(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Type* type_node = 0;
    const struct Ast_Args* args_node = 0;
    Ast_Args* res = (Ast_Args*)(ast_node(ast, AST_ARGS));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->type = type_node;
    if (ctx->tokenizer.cur->type != TOK_NAME) {
        return (void*)(0);
    }
    res->name = ctx->tokenizer.cur++;
    if (ctx->tokenizer.cur->type != TOK_COMMA) {
        return res;
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(args_node = parse_args(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->next = args_node;
    return res;
}

const Ast_Struct* parse_struct(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
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
    if (!(fields_node = parse_fields(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
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
    ParserCtx tmp_ctx;
    const struct Ast_Type* type_node = 0;
    const struct Ast_Args* args_node = 0;
    Ast_Func_proto* res = (Ast_Func_proto*)(ast_node(ast, AST_FUNC_PROTO));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(type_node = parse_type(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
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
        if (ctx->tokenizer.cur->type == TOK_CLOSE_PARENTHESIS) {
            ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
        } else {
            return (void*)(0);
        }
    } else if (ctx->tokenizer.cur->type == TOK_NAME) {
        if (args_node = parse_args(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->args = args_node;
        } else {
            return (void*)(0);
        }
    } else {
        return (void*)(0);
    }

    if (ctx->tokenizer.cur->type == TOK_CLOSE_PARENTHESIS) {
        ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    }
    return res;
}

const Ast_Func_decl* parse_func_decl(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Func_proto* func_proto_node = 0;
    Ast_Func_decl* res = (Ast_Func_decl*)(ast_node(ast, AST_FUNC_DECL));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(func_proto_node = parse_func_proto(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->proto = func_proto_node;
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    return res;
}

const Ast_Expr_num* parse_expr_num(Ast* ast, ParserCtx* ctx) {
    Ast_Expr_num* res = (Ast_Expr_num*)(ast_node(ast, AST_EXPR_NUM));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type != TOK_NUMBER) {
        return (void*)(0);
    }
    res->value = ctx->tokenizer.cur++;
    return res;
}

const Ast_Expr_add* parse_expr_add(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr* expr_node = 0;
    Ast_Expr_add* res = (Ast_Expr_add*)(ast_node(ast, AST_EXPR_ADD));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->lhs = expr_node;
    if (ctx->tokenizer.cur->type != TOK_PLUS) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->rhs = expr_node;
    return res;
}

const Ast_Expr_sub* parse_expr_sub(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr* expr_node = 0;
    Ast_Expr_sub* res = (Ast_Expr_sub*)(ast_node(ast, AST_EXPR_SUB));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->lhs = expr_node;
    if (ctx->tokenizer.cur->type != TOK_MINUS) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->rhs = expr_node;
    return res;
}

const Ast_Expr_mul* parse_expr_mul(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr* expr_node = 0;
    Ast_Expr_mul* res = (Ast_Expr_mul*)(ast_node(ast, AST_EXPR_MUL));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->lhs = expr_node;
    if (ctx->tokenizer.cur->type != TOK_ASTERISK) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->rhs = expr_node;
    return res;
}

const Ast_Expr_div* parse_expr_div(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr* expr_node = 0;
    Ast_Expr_div* res = (Ast_Expr_div*)(ast_node(ast, AST_EXPR_DIV));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->lhs = expr_node;
    if (ctx->tokenizer.cur->type != TOK_SLASH) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->rhs = expr_node;
    return res;
}

const Ast_Expr* parse_expr(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr_num* expr_num_node = 0;
    const struct Ast_Expr_add* expr_add_node = 0;
    const struct Ast_Expr_sub* expr_sub_node = 0;
    const struct Ast_Expr_div* expr_div_node = 0;
    const struct Ast_Expr_mul* expr_mul_node = 0;
    const struct Ast_Expr* expr_node = 0;
    Ast_Expr* res = (Ast_Expr*)(ast_node(ast, AST_EXPR));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type == TOK_NUMBER) {
        if (expr_num_node = parse_expr_num(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->expr = (const AstNode*)(expr_num_node);
        } else if (expr_add_node =
                       parse_expr_add(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->expr = (const AstNode*)(expr_add_node);
        } else if (expr_sub_node =
                       parse_expr_sub(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->expr = (const AstNode*)(expr_sub_node);
        } else if (expr_div_node =
                       parse_expr_div(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->expr = (const AstNode*)(expr_div_node);
        } else if (expr_mul_node =
                       parse_expr_mul(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->expr = (const AstNode*)(expr_mul_node);
        } else {
            return (void*)(0);
        }

    } else {
        return (void*)(0);
    }
    if (expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx))) {
        set_ctx(ctx, &tmp_ctx);
        res->next = expr_node;
    }
    return res;
}

const Ast_Constr_return* parse_constr_return(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Expr* expr_node = 0;
    Ast_Constr_return* res =
        (Ast_Constr_return*)(ast_node(ast, AST_CONSTR_RETURN));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type != TOK_RETURN) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(expr_node = parse_expr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->expr = expr_node;
    if (ctx->tokenizer.cur->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    return res;
}

const Ast_Constr* parse_constr(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Constr_return* constr_return_node = 0;
    const struct Ast_Constr* constr_node = 0;
    Ast_Constr* res = (Ast_Constr*)(ast_node(ast, AST_CONSTR));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(constr_return_node =
              parse_constr_return(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->constr = (const AstNode*)(constr_return_node);
    if (!(constr_node = parse_constr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return res;
    }
    set_ctx(ctx, &tmp_ctx);
    res->next = constr_node;
    return res;
}

const Ast_Func* parse_func(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Func_proto* func_proto_node = 0;
    const struct Ast_Constr* constr_node = 0;
    Ast_Func* res = (Ast_Func*)(ast_node(ast, AST_FUNC));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (!(func_proto_node = parse_func_proto(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->proto = func_proto_node;
    if (ctx->tokenizer.cur->type != TOK_OPEN_CURLY) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    if (!(constr_node = parse_constr(ast, set_ctx(&tmp_ctx, ctx)))) {
        return (void*)(0);
    }
    set_ctx(ctx, &tmp_ctx);
    res->body = constr_node;
    if (ctx->tokenizer.cur->type != TOK_CLOSE_CURLY) {
        return (void*)(0);
    }
    ctx->tokenizer.cur = ctx->tokenizer.cur + 1;
    return res;
}

const Ast_Toplevel* parse_toplevel(Ast* ast, ParserCtx* ctx) {
    ParserCtx tmp_ctx;
    const struct Ast_Struct* struct_node = 0;
    const struct Ast_Func* func_node = 0;
    const struct Ast_Func_decl* func_decl_node = 0;
    const struct Ast_Toplevel* toplevel_node = 0;
    Ast_Toplevel* res = (Ast_Toplevel*)(ast_node(ast, AST_TOPLEVEL));
    if (!res) {
        ctx->error = PARSERE_OUT_OF_MEMORY;
        return res;
    }
    ctx->cur_node = (AstNode*)(res);
    if (ctx->tokenizer.cur->type == TOK_STRUCT) {
        if (struct_node = parse_struct(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->element = (const AstNode*)(struct_node);
        } else {
            return (void*)(0);
        }
    } else if (ctx->tokenizer.cur->type == TOK_NAME) {
        if (func_node = parse_func(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->element = (const AstNode*)(func_node);
        } else if (func_decl_node =
                       parse_func_decl(ast, set_ctx(&tmp_ctx, ctx))) {
            set_ctx(ctx, &tmp_ctx);
            res->element = (const AstNode*)(func_decl_node);
        } else {
            return (void*)(0);
        }

    } else {
        return (void*)(0);
    }

    if (toplevel_node = parse_toplevel(ast, set_ctx(&tmp_ctx, ctx))) {
        set_ctx(ctx, &tmp_ctx);
        res->next = toplevel_node;
    }
    return res;
}
