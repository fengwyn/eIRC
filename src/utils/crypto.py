# Cryptography and Hashing utilities for Client use


# The Client shall create a KeyManagement Object, 
# which handles asymmetric key escrow for use in 
# both Rooms and P2P Direct messaging.

# We'll require a client_id, keytype, key_generation_mngt=auto (default),manual:
# if automatic, handled by this Object, manual; the user manages/creates 
# their keys by inserting 2 filepath containing a pub and priv keys respectively

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
import os

_AUTO = 1
_MANUAL = 0


class KeyManager:

    
    def __init__(self, keytype=_AUTO, privkey_path=None, pubkey_path=None, passwd=None):

        self.privkey = None
        self.pubkey = None


        if keytype == _MANUAL:

            if not privkey_path or not pubkey_path:
                raise ValueError("Both privkey_path and pubkey_path must be provided for manual key management")
            self._load_keys_from_files(privkey_path, pubkey_path, passwd)
        else:
            self._generate_keys()
    

    # Automatically generate RSA pair
    def _generate_keys(self):

        self.privkey = rsa.generate_private_key(
            public_exponent=65537, 
            key_size=2048
        )
        self.pubkey = self.privkey.public_key()
    

    # Load keys if using _MANUAL
    def _load_keys_from_files(self, privkey_path, pubkey_path, psswd):

        try:
            # Loads private key
            if not os.path.exists(privkey_path):
                raise FileNotFoundError(f"Private key file not found: {privkey_path}")
                
            with open(privkey_path, 'rb') as f:
                private_key_data = f.read()
                self.privkey = serialization.load_pem_private_key(
                    private_key_data,
                    password=passwd  # None by default
                )
            
            # Load public key
            if not os.path.exists(pubkey_path):
                raise FileNotFoundError(f"Public key file not found: {pubkey_path}")
                
            with open(pubkey_path, 'rb') as f:
                public_key_data = f.read()
                self.pubkey = serialization.load_pem_public_key(public_key_data)
                
        except Exception as e:
            raise RuntimeError(f"Failed to load keys from files: {str(e)}")
    

    def encrypt(self, message) -> bytes:

        if self.pubkey is None:
            raise RuntimeError("Public key not available")
            
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        ciphertext = self.pubkey.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext
    

    def decrypt(self, ciphertext) -> bytes:

        if self.privkey is None:
            raise RuntimeError("Private key not available")
            
        plaintext = self.privkey.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext
    

    # Sign with private key
    def sign(self, message) -> bytes:

        if self.privkey is None:
            raise RuntimeError("Private key not available")
            
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        signature = self.privkey.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    

    def verify_signature(self, signature, message) -> bool:

        if self.pubkey is None:
            raise RuntimeError("Public key not available")
            
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        try:
            self.pubkey.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
    
    
    # Saves the current key pair to PEM files; Password is optional for private key file
    def save_keys(self, privkey_path, pubkey_path, password=None):

        if self.privkey is None or self.pubkey is None:
            raise RuntimeError("Keys not available to save")
        
        # Serialize the private key
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
        else:
            encryption_algorithm = serialization.NoEncryption()
            
        private_pem = self.privkey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        
        # Serialize the public key
        public_pem = self.pubkey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        try:
            # Write to the files
            with open(privkey_path, 'wb') as f:
                f.write(private_pem)
                
            with open(pubkey_path, 'wb') as f:
                f.write(public_pem)
        except Exception as e:
            print(f"Error writing to PEM files: {e}")



# Usages examples
if __name__ == "__main__":
    
    # Test with auto-generated keys
    print("Testing with auto-generated keys:")
    km_auto = KeyManager(keytype=_AUTO)
    
    example = "penguin"

    message = f"Your mom is a {example}"

    print(f"Original message: {message}")
    
    # Test encryption/decryption
    ciphertext = km_auto.encrypt(message)
    decrypted = km_auto.decrypt(ciphertext)
    print(f"Encrypted message: {ciphertext}")
    print(f"Decrypted message: {decrypted.decode('utf-8')}")
    
    # Test signing/verification
    signature = km_auto.sign(message)
    is_valid = km_auto.verify_signature(signature, message)
    print(f"Signature validation: {is_valid}")
    
    # Save keys for manual loading test
    km_auto.save_keys("test_private.pem", "test_public.pem")
    
    print("\nTesting with manually loaded keys:")

    # Test with manually loaded keys
    try:
        km_manual = KeyManager(keytype=_MANUAL, 
                              privkey_path="test_private.pem", 
                              pubkey_path="test_public.pem",
                              passwd=None)
        
        # Testing if the loaded keys work the same way
        ciphertext2 = km_manual.encrypt(message)
        decrypted2 = km_manual.decrypt(ciphertext2)
        print(f"Decrypted with loaded keys: {decrypted2.decode('utf-8')}")
        
        # Cleaning up test files
        os.remove("test_private.pem")
        os.remove("test_public.pem")
        
    except Exception as e:
        print(f"Manual key loading test failed: {e}")