#!env python3.8
import sys
import zlib
from base45 import b45encode

from cose.messages import Sign1Message, CoseMessage
from cose.keys import CoseKey
from cose.headers import Algorithm, KID
from cose.curves import P256
from cose.algorithms import Es256, EdDSA
from cose.keys.keyparam import KpKty, KpAlg, EC2KpD, EC2KpX, EC2KpY, EC2KpCurve
from cose.keys.keytype import KtyEC2
from cose.keys.keyops import SignOp, VerifyOp
from cose.keys.keyparam import KpKty, KpKeyOps
from cose.keys.keytype import KtyOKP
from cose.messages import Sign1Message

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key


# Note - we only need the public key for the KeyID calculation - we're not actually using it.
with open("dsc-worker.pem", "rb") as file:
    pem = file.read()
cert = x509.load_pem_x509_certificate(pem)
fingerprint = cert.fingerprint(hashes.SHA256())
keyid = fingerprint[-8:]

# Read in the private key that we use to actually sign this
#
with open("dsc-worker.key", "rb") as file:
    pem = file.read()
keyfile = load_pem_private_key(pem, password=None)
priv = keyfile.private_numbers().private_value.to_bytes(32, byteorder="big")

# Prepare a message to sign; specifying algorithm and keyid
# that we (will) use
#
msg = Sign1Message(
    phdr={Algorithm: Es256, KID: keyid}, payload="Hello World!".encode("utf-8")
)

# Create the signing key - use ecdsa-with-SHA256
# and NIST P256 / secp256r1
#
cose_key = {
    KpKty: KtyEC2,
    KpAlg: Es256,  # ecdsa-with-SHA256
    EC2KpCurve: P256,  # Ought to be pk.curve - but the two libs clash
    EC2KpD: priv,
}

# Encode the message (which includes signing)
#
msg.key = CoseKey.from_dict(cose_key)
encoded = msg.encode()

# Compress with ZLIB
#
out = zlib.compress(encoded, 9)
# sys.stdout.buffer.write(out)

# And base45 encode the result
#
b45 = b45encode(out)

sys.stdout.write(b45)
