#include <ast.h>
const struct Ast_Type* parse_type(const struct Token* beg,
                                  const struct Token* end) {
    const struct Token* cur_tok = beg;
    if ((cur_tok++)->type != TOK_NAME) {
        return (void*)(0);
    }
    struct Ast_Type* res = malloc(sizeof *res);
    assert(res);
    *res = (struct Ast_Type){0};
    return res;
}

const struct Ast_Field* parse_field(const struct Token* beg,
                                    const struct Token* end) {
    const struct Token* cur_tok = beg;
    struct Ast_Type* node = parse_type(cur_tok, end);
    if (!node) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_NAME) {
        return (void*)(0);
    }
    struct Ast_Field* res = malloc(sizeof *res);
    assert(res);
    *res = (struct Ast_Field){0};
    return res;
}

const struct Ast_Struct* parse_struct(const struct Token* beg,
                                      const struct Token* end) {
    const struct Token* cur_tok = beg;
    if ((cur_tok++)->type != TOK_STRUCT) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_NAME) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_OPEN_CURLY) {
        return (void*)(0);
    }
    struct Ast_Field* node = parse_field(cur_tok, end);
    if (!node) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_CLOSE_CURLY) {
        return (void*)(0);
    }
    if ((cur_tok++)->type != TOK_SEMICOLON) {
        return (void*)(0);
    }
    struct Ast_Struct* res = malloc(sizeof *res);
    assert(res);
    *res = (struct Ast_Struct){0};
    return res;
}

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
        ast->allocator->free(to_free);
    }
    ast->allocator->free(ast);
}
