#include <ctype.h>
#include <string.h>
#include <token.h>
struct Token token(TokenType type, const char* beg, const char* end);
struct Token number_token(const char* beg, const char* end);
struct Token space_token(const char* beg, const char* end);
struct Token return_token(const char* beg, const char* end);
struct Token struct_token(const char* beg, const char* end);
struct Token name_token(const char* beg, const char* end);

struct Token token(TokenType type, const char* beg, const char* end) {
    return (struct Token){
        .type = type,
        .beg = beg,
        .end = end,
    };
}

struct Token get_token(const char* beg, const char* end) {
    if (beg == end) {
        return token(TOK_EOF, beg, beg);
    }
    switch (*beg) {
        case '0':
            return number_token(beg, end);
        case '1':
            return number_token(beg, end);
        case '2':
            return number_token(beg, end);
        case '3':
            return number_token(beg, end);
        case '4':
            return number_token(beg, end);
        case '5':
            return number_token(beg, end);
        case '6':
            return number_token(beg, end);
        case '7':
            return number_token(beg, end);
        case '8':
            return number_token(beg, end);
        case '9':
            return number_token(beg, end);
        case '{':
            return token(TOK_OPEN_CURLY, beg, beg + 1);
        case '}':
            return token(TOK_CLOSE_CURLY, beg, beg + 1);
        case '(':
            return token(TOK_OPEN_PARENTHESIS, beg, beg + 1);
        case ')':
            return token(TOK_CLOSE_PARENTHESIS, beg, beg + 1);
        case ';':
            return token(TOK_SEMICOLON, beg, beg + 1);
        case ',':
            return token(TOK_COMMA, beg, beg + 1);
        case ' ':
            return space_token(beg, end);
        case '\n':
            return space_token(beg, end);
        case '+':
            return token(TOK_PLUS, beg, beg + 1);
        case '-':
            return token(TOK_MINUS, beg, beg + 1);
        case '*':
            return token(TOK_ASTERISK, beg, beg + 1);
        case '/':
            return token(TOK_SLASH, beg, beg + 1);
    }
    // TODO: STRUCT is subset of NAME
    // We should not handle STRUCT if token is not NAME
    struct Token cur_token = return_token(beg, end);
    if (cur_token.type == TOK_RETURN) {
        return cur_token;
    }
    cur_token = struct_token(beg, end);
    if (cur_token.type == TOK_STRUCT) {
        return cur_token;
    }
    cur_token = name_token(beg, end);
    if (cur_token.type == TOK_NAME) {
        return cur_token;
    }
    return token(TOK_EOF, beg, beg + 1);
}

struct Token number_token(const char* beg, const char* end) {
    const char* cur = beg;
    if (cur == end || !isdigit(*cur)) {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (cur != end && isdigit(*cur)) {
        cur = cur + 1;
    }
    return token(TOK_NUMBER, beg, cur);
}

struct Token space_token(const char* beg, const char* end) {
    const char* cur = beg;
    if (cur == end || (*cur != ' ' && *cur != '\n')) {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (cur != end && (*cur == ' ' || *cur == '\n')) {
        cur = cur + 1;
    }
    return token(TOK_SPACE, beg, cur);
}

struct Token return_token(const char* beg, const char* end) {
    const char* cur = beg;
    if (end - cur < 6 || memcmp(cur, "return", 6)) {
        return token(TOK_EOF, beg, cur);
    }
    return token(TOK_RETURN, beg, cur + 6);
}

struct Token struct_token(const char* beg, const char* end) {
    const char* cur = beg;
    if (end - cur < 6 || memcmp(cur, "struct", 6)) {
        return token(TOK_EOF, beg, cur);
    }
    return token(TOK_STRUCT, beg, cur + 6);
}

struct Token name_token(const char* beg, const char* end) {
    const char* cur = beg;
    if (cur == end || (!isalpha(*cur) && *cur != '_')) {
        return token(TOK_EOF, beg, cur);
    }
    cur = cur + 1;
    while (cur != end && (isalnum(*cur) || *cur == '_')) {
        cur = cur + 1;
    }
    return token(TOK_NAME, beg, cur);
}

const char* token_type_str(TokenType type) {
    switch (type) {
        case TOK_EOF:
            return "EOF";
        case TOK_NAME:
            return "NAME";
        case TOK_STRUCT:
            return "STRUCT";
        case TOK_RETURN:
            return "RETURN";
        case TOK_NUMBER:
            return "NUMBER";
        case TOK_OPEN_CURLY:
            return "OPEN_CURLY";
        case TOK_CLOSE_CURLY:
            return "CLOSE_CURLY";
        case TOK_OPEN_PARENTHESIS:
            return "OPEN_PARENTHESIS";
        case TOK_CLOSE_PARENTHESIS:
            return "CLOSE_PARENTHESIS";
        case TOK_SEMICOLON:
            return "SEMICOLON";
        case TOK_COMMA:
            return "COMMA";
        case TOK_SPACE:
            return "SPACE";
        case TOK_PLUS:
            return "PLUS";
        case TOK_MINUS:
            return "MINUS";
        case TOK_ASTERISK:
            return "ASTERISK";
        case TOK_SLASH:
            return "SLASH";
        default:
            return 0;
    }
}

void token_dump(struct Token token, FILE* out) {
    fprintf(out, "%s \"", token_type_str(token.type));
    for (const char* cur = token.beg; cur != token.end; cur = cur + 1) {
        if (*cur == '\"' || *cur == '\\' || *cur == '\'') {
            fprintf(out, "\\%c", *cur);
        } else if (*cur == '\n') {
            fprintf(out, "\\n");
        } else if (ispunct(*cur) || isalnum(*cur) || *cur == ' ') {
            fprintf(out, "%c", *cur);
        } else {
            fprintf(out, "\\x%02x", *cur);
        }
    }
    fprintf(out, "\"");
}
