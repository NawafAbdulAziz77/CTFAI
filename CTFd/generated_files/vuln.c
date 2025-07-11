```c
#include <stdio.h>
#include <string.h>

void vulnerable_function() {
    char buffer[64];
    printf("Masukkan input Anda: ");
    gets(buffer);
    printf("Anda memasukkan: %s\n", buffer);
}

int main() {
    vulnerable_function();
    return 0;
}
```