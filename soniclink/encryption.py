"""
Encryption module for SonicLink using AES-256 and RSA.
"""

import os
import logging
from typing import Optional, Tuple
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)


class CryptoManager:
    """
    Cryptographic manager for SonicLink.
    
    Handles AES-256 encryption/decryption with RSA key exchange.
    """
    
    def __init__(self):
        """Initialize the crypto manager."""
        self.aes_key_size = 32  # 256 bits
        self.rsa_key_size = 2048
        self.iv_size = 16  # AES block size
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair.
        
        Returns:
            Tuple of (private_key, public_key) as bytes
        """
        try:
            # Generate RSA key pair
            key = RSA.generate(self.rsa_key_size)
            
            # Export keys
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            
            logger.info(f"Generated RSA key pair ({self.rsa_key_size} bits)")
            return private_key, public_key
            
        except Exception as e:
            logger.error(f"Failed to generate key pair: {e}")
            raise
    
    def save_key_pair(self, private_key: bytes, public_key: bytes, 
                     private_path: str = "private_key.pem",
                     public_path: str = "public_key.pem"):
        """
        Save RSA key pair to files.
        
        Args:
            private_key: Private key bytes
            public_key: Public key bytes
            private_path: Path to save private key
            public_path: Path to save public key
        """
        try:
            with open(private_path, 'wb') as f:
                f.write(private_key)
            
            with open(public_path, 'wb') as f:
                f.write(public_key)
            
            logger.info(f"Saved key pair to {private_path} and {public_path}")
            
        except Exception as e:
            logger.error(f"Failed to save key pair: {e}")
            raise
    
    def load_private_key(self, key_path: str) -> bytes:
        """
        Load private key from file.
        
        Args:
            key_path: Path to private key file
            
        Returns:
            Private key as bytes
        """
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            # Validate key
            RSA.import_key(key_data)
            
            logger.info(f"Loaded private key from {key_path}")
            return key_data
            
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise
    
    def load_public_key(self, key_path: str) -> bytes:
        """
        Load public key from file.
        
        Args:
            key_path: Path to public key file
            
        Returns:
            Public key as bytes
        """
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            # Validate key
            RSA.import_key(key_data)
            
            logger.info(f"Loaded public key from {key_path}")
            return key_data
            
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise
    
    def encrypt(self, data: bytes, recipient_public_key: bytes) -> bytes:
        """
        Encrypt data using AES-256 with RSA key exchange.
        
        Args:
            data: Data to encrypt
            recipient_public_key: Recipient's RSA public key
            
        Returns:
            Encrypted data as bytes
        """
        try:
            # Generate random AES key
            aes_key = get_random_bytes(self.aes_key_size)
            
            # Generate random IV
            iv = get_random_bytes(self.iv_size)
            
            # Encrypt data with AES
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            padded_data = pad(data, AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Encrypt AES key with RSA
            rsa_key = RSA.import_key(recipient_public_key)
            rsa_cipher = PKCS1_OAEP.new(rsa_key)
            encrypted_key = rsa_cipher.encrypt(aes_key)
            
            # Combine encrypted key, IV, and encrypted data
            result = (
                len(encrypted_key).to_bytes(2, 'big') +  # Key length (2 bytes)
                encrypted_key +                          # Encrypted AES key
                iv +                                     # IV
                encrypted_data                           # Encrypted data
            )
            
            logger.info(f"Encrypted {len(data)} bytes to {len(result)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: bytes, private_key: bytes) -> Optional[bytes]:
        """
        Decrypt data using AES-256 with RSA key exchange.
        
        Args:
            encrypted_data: Encrypted data
            private_key: Recipient's RSA private key
            
        Returns:
            Decrypted data, or None if decryption failed
        """
        try:
            # Extract components
            key_length = int.from_bytes(encrypted_data[:2], 'big')
            encrypted_key = encrypted_data[2:2+key_length]
            iv = encrypted_data[2+key_length:2+key_length+self.iv_size]
            data = encrypted_data[2+key_length+self.iv_size:]
            
            # Decrypt AES key with RSA
            rsa_key = RSA.import_key(private_key)
            rsa_cipher = PKCS1_OAEP.new(rsa_key)
            aes_key = rsa_cipher.decrypt(encrypted_key)
            
            # Decrypt data with AES
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(data)
            decrypted_data = unpad(decrypted_padded, AES.block_size)
            
            logger.info(f"Decrypted {len(encrypted_data)} bytes to {len(decrypted_data)} bytes")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_symmetric(self, data: bytes, key: bytes = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256 with a symmetric key.
        
        Args:
            data: Data to encrypt
            key: AES key (if None, generates a random key)
            
        Returns:
            Tuple of (encrypted_data, key)
        """
        try:
            if key is None:
                key = get_random_bytes(self.aes_key_size)
            
            iv = get_random_bytes(self.iv_size)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = pad(data, AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV and encrypted data
            result = iv + encrypted_data
            
            logger.info(f"Symmetric encryption: {len(data)} -> {len(result)} bytes")
            return result, key
            
        except Exception as e:
            logger.error(f"Symmetric encryption failed: {e}")
            raise
    
    def decrypt_symmetric(self, encrypted_data: bytes, key: bytes) -> Optional[bytes]:
        """
        Decrypt data using AES-256 with a symmetric key.
        
        Args:
            encrypted_data: Encrypted data
            key: AES key
            
        Returns:
            Decrypted data, or None if decryption failed
        """
        try:
            iv = encrypted_data[:self.iv_size]
            data = encrypted_data[self.iv_size:]
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(data)
            decrypted_data = unpad(decrypted_padded, AES.block_size)
            
            logger.info(f"Symmetric decryption: {len(encrypted_data)} -> {len(decrypted_data)} bytes")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Symmetric decryption failed: {e}")
            return None
    
    def hash_data(self, data: bytes) -> bytes:
        """
        Create a hash of data for integrity checking.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash as bytes
        """
        import hashlib
        return hashlib.sha256(data).digest()
    
    def verify_integrity(self, data: bytes, expected_hash: bytes) -> bool:
        """
        Verify data integrity using hash.
        
        Args:
            data: Data to verify
            expected_hash: Expected hash
            
        Returns:
            True if hash matches
        """
        actual_hash = self.hash_data(data)
        return actual_hash == expected_hash 