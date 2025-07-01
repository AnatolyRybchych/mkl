#include <token.h>
struct Token get_token(const char *beg, const char *end) {
    if (beg == end) {
        return (struct Token){
            .type = TOK_EOF,
            .beg = beg,
            .end = beg,
        };
    }
    const char *tok_end = beg + 1;
    switch (*beg) {
        case '{':
            return (struct Token){
                .type = TOK_OPEN_CURLY,
                .beg = beg,
                .end = tok_end,
            };
        case '}':
            return (struct Token){
                .type = TOK_CLOSE_CURLY,
                .beg = beg,
                .end = tok_end,
            };
        case '(':
            return (struct Token){
                .type = TOK_OPEN_PARENTHESIS,
                .beg = beg,
                .end = tok_end,
            };
        case ')':
            return (struct Token){
                .type = TOK_CLOSE_PARENTHESIS,
                .beg = beg,
                .end = tok_end,
            };
        case ';':
            return (struct Token){
                .type = TOK_SEMICOLON,
                .beg = beg,
                .end = tok_end,
            };
    }
    // TODO: add this logic under the switch case
    if (strncmp(tok_end, "++", end - tok_end) == 0) {
        return (struct Token){
            .type = TOK_INCREMENT,
            .beg = beg,
            .end = beg + 1,
        };
    }
    // The get_token function is not ment to fail.
    // Return EOF with len != 0 for unknown token
    return (struct Token){
        .type = TOK_EOF,
        .beg = beg,
        .end = beg + 1,
    };
}
