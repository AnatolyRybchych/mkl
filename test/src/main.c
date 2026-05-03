#include <errno.h>
#include <string.h>
#include <token.h>
#include <ast.h>

#include <stdio.h>
#include <malloc.h>
#include <stdbool.h>

void *malloc_alloc(Allocator *self, unsigned long size) {
    (void)self;
    return malloc(size);
}

void malloc_free(Allocator *self, void *ptr) {
    (void)self;
    free(ptr);
}

static Allocator *malloc_allocator = &(Allocator) {
    .alloc = malloc_alloc,
    .free = malloc_free,
};

int read_entire_file(const char *path, size_t *filesize, char **data) {
    FILE *file = fopen(path, "r");
    if(file == NULL) {
        return errno;
    }

    fseek(file, 0, SEEK_END);
    *filesize = ftell(file);
    fseek(file, 0, SEEK_SET);

    *data = malloc(*filesize);
    if (!data) {
        fclose(file);
        return errno;
    }

    fread(*data, 1, *filesize, file);
    if (ferror(file)) {
        fclose(file);
        return errno;
    }

    return  0;
}

int tokenize(size_t len, const char src[len], size_t *cnt, Token **tokens) {
    Token *res = NULL;
    size_t cur_cnt = 0, cur_bufsize = 0;

    for (const char *cur = src, *end = src + len;;) {
        Token tok = get_token(cur, end);

        if (cur_bufsize == cur_cnt) {
            cur_bufsize = cur_bufsize * 2 + 1;
            Token *new_res = realloc(res, sizeof(Token[cur_bufsize]));
            if (!new_res) {
                free(res);
                return ENOMEM;
            }

            res = new_res;
        }
        
        if (tok.type != TOK_SPACE) {
            res[cur_cnt++] = tok;
        }

        token_dump(tok, stderr);
        fprintf(stderr, "\n");

        if(tok.type == TOK_EOF) {
            break;
        }

        cur = tok.end;
    }

    *tokens = res;
    *cnt = cur_cnt;
    return 0;
}

int main(void) {
    const char *source_file = "test";

    char *src = NULL;
    size_t filesize = 0;
    int error = read_entire_file(source_file, &filesize, &src);
    if (error) {
        fprintf(stderr, "ERROR: could not open a file:\n%s: %s", source_file, strerror(error));
        return 1;
    }

    size_t cnt_tokens = 0;
    Token *tokens;
    error = tokenize(filesize, src, &cnt_tokens, &tokens);
    if (error) {
        fprintf(stderr, "ERROR: failed to parse a file:\n%s: %s", source_file, strerror(error));
        return 1;
    }

    struct ParserCtx ctx = {
        .tokenizer = {
            .beg = tokens,
            .cur = tokens,
            .end = tokens + cnt_tokens
        }
    };

    Ast *ast = ast_init(malloc_allocator);
    if (!ast) {
        fprintf(stderr, "ERROR: failed initialize ast:\n%s: %s", source_file, strerror(ENOMEM));
        return 1;
    }

    const Ast_Struct *ast_struct = parse_struct(ast, &ctx);

    if (!ast_struct) {
        fprintf(stderr, "ERROR: failed to parse struct\n");
        return 1;
    }

    printf("struct %.*s\n", ast_struct->name->end - ast_struct->name->beg, ast_struct->name->beg);
    printf("    %.*s %.*s.%.*s\n", 
        ast_struct->fields->type->name->end - ast_struct->fields->type->name->beg, ast_struct->fields->type->name->beg,
        ast_struct->name->end - ast_struct->name->beg, ast_struct->name->beg,
        ast_struct->fields->name->end - ast_struct->fields->name->beg, ast_struct->fields->name->beg);

    ast_clean(ast);
}
