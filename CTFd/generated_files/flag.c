#include <stdio.h>
#include <string.h>
#include <unistd.h>

char secret[10];

void vulnerable_function(char* input) {
    printf("Input: %s\n", input);
    strcpy(secret, input);
}

int main(int argc, char argv) {
    if (argc != 2) {
        printf("Usage: %s <input>\n", argv[0]);
        return -1;
    }

    vulnerable_function(argv[1]);

    printf("Secret: %s\n", secret);

    return 0;
}