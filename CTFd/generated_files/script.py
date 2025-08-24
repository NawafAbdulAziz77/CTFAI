import string

def caesar_cipher(plaintext, key):
    ciphertext = ""
    for char in plaintext:
        if char in string.ascii_uppercase:
            ascii_pos = ord(char) + key
            ciphertext += string.ascii_uppercase[ascii_pos % 26]
        elif char in string.ascii_lowercase:
            ascii_pos = ord(char) + key
            ciphertext += string.ascii_lowercase[ascii_pos % 26]
        elif char == " ":
            ciphertext += " "
        else:
            ciphertext += char
    return ciphertext

plaintext = "Capture The Flag Indonesia 2022"
key = 3
ciphertext = caesar_cipher(plaintext, key)
print(ciphertext)