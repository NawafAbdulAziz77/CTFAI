```python
def caesar_cipher(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            new_char = chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            result += new_char
        else:
            result += char
    return result

text = "LXFOPVQNTR WXUJDHNQIO PRRDORHGZS VFERFWVQJ"
shift = 3
flag = caesar_cipher(text, shift)
print(flag)