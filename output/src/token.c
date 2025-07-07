#include <token.h>
struct Token token(TokenType type, const char *beg, const char *end);
struct Token space_token(const char *beg, const char *end);
struct Token increment_token(const char *beg, const char *end);

struct Token token(TokenType type, const char *beg, const char *end) {
    return (struct Token){
        .type = type,
        .beg = beg,
        .end = end,
    };
}

struct Token get_token(const char *beg, const char *end) {
    if (beg == end) {
        return token(TOK_EOF, beg, beg);
    }
    const char *tok_end = beg + 1;
    switch (*beg) {
        case '{':
            return token(TOK_OPEN_CURLY, beg, tok_end);
        case '}':
            return token(TOK_CLOSE_CURLY, beg, tok_end);
        case '(':
            return token(TOK_OPEN_PARENTHESIS, beg, tok_end);
        case ')':
            return token(TOK_CLOSE_PARENTHESIS, beg, tok_end);
        case ';':
            return token(TOK_SEMICOLON, beg, tok_end);
        case ' ':
            return space_token(beg, end);
        case '\n':
            return space_token(beg, end);
        case '+':
            return increment_token(beg, end);
    }
    // TODO: handle overlapping token NAME
    // TODO: handle overlapping token STRUCT
    // The get_token function is not meant to fail.
    // Return EOF with len != 0 for unknown token
    return token(TOK_EOF, beg, beg + 1);
}

struct Token space_token(const char *beg, const char *end) {
    const char *cur =
        beg;  // TODO: replace repetitive ifs with strncmp if possible
    if (cur == end || *cur != ' ' || *cur != '\n') {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;  // TODO: move the first if statement in the loop under the
                    // loop condition
    // TODO: move the last "cur += 1" under the for increment expression
    while (1) {  // TODO: replace repetitive ifs with strncmp if possible
        if (cur == end || *cur != ' ' || *cur != '\n') {
            return token(TOK_SPACE, beg, cur);
        }
        cur = cur + 1;
    }
}

struct Token increment_token(const char *beg, const char *end) {
    const char *cur =
        beg;  // TODO: replace repetitive ifs with strncmp if possible
    if (cur == end || *cur != '+') {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;  // TODO: replace repetitive ifs with strncmp if possible
    if (cur == end || *cur != '+') {
        return token(TOK_EOF, beg, cur);
    }
    return token(TOK_INCREMENT, beg, cur);
}
