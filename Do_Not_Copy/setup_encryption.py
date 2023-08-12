from securedict import DecryptDicts, EncryptDicts
from mysecrets import secrets

ed = EncryptDicts()
ed.new_key("refKey.txt")
# ed.read_key("Do_Not_Copy/RealRefKey.txt")
ed.encrypt_dict(secrets)
ed.write_dict("secretsecrets.py")
