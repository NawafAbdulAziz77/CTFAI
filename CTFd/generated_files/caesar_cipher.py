def caesar_cipher(text, shift):
 result = ""
 for char in text:
 if char.isalpha():
 new_char = chr((ord(char) + shift - ord('A')) % 26 + ord('A'))
 else:
 new_char = char
 result += new_char
 return result

text = "KXUH VKHUR PLZR QEBDI ZRQVP"
shift = 3
print(caesar_cipher(text, shift))