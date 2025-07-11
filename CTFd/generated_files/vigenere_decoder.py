```python
def vigenere_decrypt(ciphertext, key):
    decrypted_text = ""
    key_length = len(key)
    for i, char in enumerate(ciphertext):
        if char.isalpha():
            shift = ord(key[i % key_length].lower()) - ord('a')
            decrypted_char = chr((ord(char.lower()) - ord('a') - shift) % 26 + ord('a'))
            decrypted_text += decrypted_char
        else:
            decrypted_text += char
    return decrypted_text

ciphertext = "Rijvs Uyqvo"
key = "CTF"
plaintext = vigenere_decrypt(ciphertext, key)
print("Decrypted Text:", plaintext)
```