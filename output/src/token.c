#include <token.h>
struct Token get_token(const char *beg, const char *end) {
    switch (*beg) {
        case '{':
            return (struct Token){
                .type = TOK_OPEN_CURLY,
                .beg = beg,
                .end = beg + 1,
            };
        case '}':
            return (struct Token){
                .type = TOK_CLOSE_CURLY,
                .beg = beg,
                .end = beg + 1,
            };
        case '(':
            return (struct Token){
                .type = TOK_OPEN_PARENTHESIS,
                .beg = beg,
                .end = beg + 1,
            };
        case ')':
            return (struct Token){
                .type = TOK_CLOSE_PARENTHESIS,
                .beg = beg,
                .end = beg + 1,
            };
        case ';':
            return (struct Token){
                .type = TOK_SEMICOLON,
                .beg = beg,
                .end = beg + 1,
            };
    }
}
