```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[100];
    sprintf(buffer, "Input anda: %s\n", input);
    puts(buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input>\n", argv[0]);
        return 1;
    }

    vulnerable_function(argv[1]);
    return 0;
}
```