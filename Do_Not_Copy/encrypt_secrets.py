import argparse
from securedict import EncryptDicts
from mysecrets import secrets

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--reencrypt", action="store", help="Reencrypt secrets from mysecrets.py using existing refKey.txt", default=0, type=int)
args = parser.parse_args()

ed = EncryptDicts()
if args.reencrypt == 0:
    ed.new_key("refKey.txt")
else:
    ed.read_key("refKey.txt")
ed.encrypt_dict(secrets)
ed.write_dict("../secretsecrets.py")
