```python
from collections import Counter

def caesar_cipher_decode(text, shift):
    decrypted_text = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            decrypted_text += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
        else:
            decrypted_text += char

    return decrypted_text

text = open("message.txt", "r").read()
frequency = Counter(text)
max_frequency = max(frequency.values())
for shift in range(1, 26):
    for char, freq in frequency.items():
        if freq != max_frequency:
            break
        if char != 'e' and char != 't' and char != 'a' and char != 'o' and char != 'i' and char != 'n':
            key = shift
            break
    if key:
        break

flag = caesar_cipher_decode(text, key)
print(flag)
```