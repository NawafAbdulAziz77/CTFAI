import base64
def decrypt_rot13(text):
 return base64.b16encode(base64.b64decode(text[::-1].encode('ascii'))[::-1]).decode('ascii')
text = "Jryybire gur jbeqf bs lbh unir cynpr lbh pbeerpg."
print(decrypt_rot13(text))