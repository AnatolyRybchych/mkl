#include <token.h>
struct Token token(TokenType type, const char *beg, const char *end);
struct Token struct_token(const char *beg, const char *end);
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
        case 's':
            return struct_token(beg, end);
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
    // The get_token function is not meant to fail.
    // Return EOF with len != 0 for unknown token
    return token(TOK_EOF, beg, beg + 1);
}

struct Token struct_token(const char *beg, const char *end) {
    const char *cur = beg;
    if (end - cur < 6 || memcmp(cur, "struct", 6)) {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 6;
    return token(TOK_STRUCT, beg, cur);
}

struct Token space_token(const char *beg, const char *end) {
    const char *cur = beg;
    if (cur == end || *cur != ' ' || *cur != '\n') {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (!(cur == end || *cur != ' ' || *cur != '\n')) {
        cur = cur + 1;
    }
    return token(TOK_SPACE, beg, cur);
}

struct Token increment_token(const char *beg, const char *end) {
    const char *cur = beg;
    if (end - cur < 2 || memcmp(cur, "++", 2)) {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 2;
    return token(TOK_INCREMENT, beg, cur);
}
