#include <token.h>
struct Token token(TokenType type, const char *beg, const char *end);
struct Token space_token(const char *beg, const char *end);
struct Token increment_token(const char *beg, const char *end);
struct Token name_or_struct_token(const char *beg, const char *end);

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
        case 'A':
            return name_or_struct_token(beg, end);
        case 'B':
            return name_or_struct_token(beg, end);
        case 'C':
            return name_or_struct_token(beg, end);
        case 'D':
            return name_or_struct_token(beg, end);
        case 'E':
            return name_or_struct_token(beg, end);
        case 'F':
            return name_or_struct_token(beg, end);
        case 'G':
            return name_or_struct_token(beg, end);
        case 'H':
            return name_or_struct_token(beg, end);
        case 'I':
            return name_or_struct_token(beg, end);
        case 'J':
            return name_or_struct_token(beg, end);
        case 'K':
            return name_or_struct_token(beg, end);
        case 'L':
            return name_or_struct_token(beg, end);
        case 'M':
            return name_or_struct_token(beg, end);
        case 'N':
            return name_or_struct_token(beg, end);
        case 'O':
            return name_or_struct_token(beg, end);
        case 'P':
            return name_or_struct_token(beg, end);
        case 'Q':
            return name_or_struct_token(beg, end);
        case 'R':
            return name_or_struct_token(beg, end);
        case 'S':
            return name_or_struct_token(beg, end);
        case 'T':
            return name_or_struct_token(beg, end);
        case 'U':
            return name_or_struct_token(beg, end);
        case 'V':
            return name_or_struct_token(beg, end);
        case 'W':
            return name_or_struct_token(beg, end);
        case 'X':
            return name_or_struct_token(beg, end);
        case 'Y':
            return name_or_struct_token(beg, end);
        case 'Z':
            return name_or_struct_token(beg, end);
        case '_':
            return name_or_struct_token(beg, end);
        case 'a':
            return name_or_struct_token(beg, end);
        case 'b':
            return name_or_struct_token(beg, end);
        case 'c':
            return name_or_struct_token(beg, end);
        case 'd':
            return name_or_struct_token(beg, end);
        case 'e':
            return name_or_struct_token(beg, end);
        case 'f':
            return name_or_struct_token(beg, end);
        case 'g':
            return name_or_struct_token(beg, end);
        case 'h':
            return name_or_struct_token(beg, end);
        case 'i':
            return name_or_struct_token(beg, end);
        case 'j':
            return name_or_struct_token(beg, end);
        case 'k':
            return name_or_struct_token(beg, end);
        case 'l':
            return name_or_struct_token(beg, end);
        case 'm':
            return name_or_struct_token(beg, end);
        case 'n':
            return name_or_struct_token(beg, end);
        case 'o':
            return name_or_struct_token(beg, end);
        case 'p':
            return name_or_struct_token(beg, end);
        case 'q':
            return name_or_struct_token(beg, end);
        case 'r':
            return name_or_struct_token(beg, end);
        case 's':
            return name_or_struct_token(beg, end);
        case 't':
            return name_or_struct_token(beg, end);
        case 'u':
            return name_or_struct_token(beg, end);
        case 'v':
            return name_or_struct_token(beg, end);
        case 'w':
            return name_or_struct_token(beg, end);
        case 'x':
            return name_or_struct_token(beg, end);
        case 'y':
            return name_or_struct_token(beg, end);
        case 'z':
            return name_or_struct_token(beg, end);
    }
    // The get_token function is not meant to fail.
    // Return EOF with len != 0 for unknown token
    return token(TOK_EOF, beg, beg + 1);
}

struct Token space_token(const char *beg, const char *end) {
    const char *cur = beg;
    if (cur == end || *cur == ' ' || *cur == '\n') {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (!(cur == end || *cur == ' ' || *cur == '\n')) {
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

struct Token name_or_struct_token(const char *beg, const char *end) {
    const char *cur = beg;
    if (cur == end || isalpha(*cur) || *cur == '_') {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (!(cur == end || isalnum(*cur) || *cur == '_')) {
        cur = cur + 1;
    }
    return token(TOK_NAME, beg, cur);
}
