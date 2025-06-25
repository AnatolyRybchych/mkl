#ifndef TOKENIZER_H
#define TOKENIZER_H

typedef enum {
    END_OF_FILE,
    TOK_NAME,
    TOK_STRUCT,
    TOK_OPEN_CURLY,
    TOK_CLOSE_CURLY,
    TOK_OPEN_PARENTHESIS,
    TOK_CLOSE_PARENTHESIS,
    TOK_SEMICOLON,
    TOK_SPACE
} TokenType;

typedef struct Token Token;
struct Token {
    TokenType type;
    const char *beg;
    const char *end;
};

#endif  // TOKENIZER_H