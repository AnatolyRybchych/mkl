#ifndef TOKENIZER_H
#define TOKENIZER_H

#include <stdio.h>
typedef enum {
    TOK_EOF,
    TOK_NAME,
    TOK_STRUCT,
    TOK_OPEN_CURLY,
    TOK_CLOSE_CURLY,
    TOK_OPEN_PARENTHESIS,
    TOK_CLOSE_PARENTHESIS,
    TOK_SEMICOLON,
    TOK_COMMA,
    TOK_SPACE
} TokenType;

typedef struct Token Token;
struct Token {
    TokenType type;
    const char* beg;
    const char* end;
};

struct Token get_token(const char* beg, const char* end);
const char* token_type_str(TokenType type);
void token_dump(struct Token token, FILE* out);

#endif  // TOKENIZER_H