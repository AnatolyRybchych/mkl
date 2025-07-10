#include <token.h>

#include <stdio.h>
#include <malloc.h>
#include <stdbool.h>

int main(void) {
    const char *source_file = "test";

    FILE *file = fopen(source_file, "r");
    if(file == NULL) {
        perror("fopen");
        return 1;
    }

    fseek(file, 0, SEEK_END);
    size_t filesize = ftell(file);
    fseek(file, 0, SEEK_SET);

    char *source = malloc(filesize);
    fread(source, 1, filesize, file);
    char *source_end = source + filesize;

    const char *cur = source;
    while (true) {
        Token tok = get_token(cur, source_end);

        token_dump(tok, stdout);
        printf("\n");

        if(tok.type == TOK_EOF) {
            break;
        }

        cur = tok.end;
    }
}
