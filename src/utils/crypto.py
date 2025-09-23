# Cryptography and Hashing utilities for Client use


# The Client shall create a KeyManagement Object, 
# which handles asymmetric key escrow for use in 
# both Rooms and P2P Direct messaging.

# We'll require a client_id, keytype, key_generation_mngt=auto (default),manual:
# if automatic, handled by this Object, manual; the user manages/creates 
# their keys by inserting 2 filepath containing a pub and priv keys respectively
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# Generate keys
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

M = b"Secret message"

# --- Encryption: Public Key Encrypt, Private Key Decrypt ---
ciphertext = public_key.encrypt(
    M,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

plaintext = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print("Decrypted:", plaintext)

# --- Signature: Private Key Sign, Public Key Verify ---
signature = private_key.sign(
    M,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# Verification (raises InvalidSignature if tampered)
public_key.verify(
    signature,
    M,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)
print("Signature verified!")
