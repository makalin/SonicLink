"""
Core SonicLink classes for sending and receiving data via ultrasonic communication.
"""

import time
import logging
from typing import Optional, Union, Dict, Any
from pathlib import Path

from .compression import HuffmanCompressor
from .encryption import CryptoManager
from .modulation import OFDMModulator, OFDMDemodulator
from .audio import AudioManager
from .utils import FrequencyRange, Config

logger = logging.getLogger(__name__)


class SonicLinkSender:
    """
    Main class for sending data via ultrasonic communication.
    
    Handles the complete pipeline: compression -> encryption -> modulation -> transmission
    """
    
    def __init__(self, 
                 freq_range: FrequencyRange = None,
                 bitrate: int = 80000,
                 config: Config = None):
        """
        Initialize the SonicLink sender.
        
        Args:
            freq_range: Frequency range for transmission (default: 18-22 kHz)
            bitrate: Target bitrate in bits per second
            config: Configuration object
        """
        self.config = config or Config()
        self.freq_range = freq_range or FrequencyRange(18000, 22000)
        self.bitrate = bitrate
        
        # Initialize components
        self.compressor = HuffmanCompressor()
        self.crypto = CryptoManager()
        self.modulator = OFDMModulator(
            freq_range=self.freq_range,
            bitrate=self.bitrate,
            config=self.config
        )
        self.audio = AudioManager(config=self.config)
        
        logger.info(f"SonicLinkSender initialized with freq_range={self.freq_range}, bitrate={self.bitrate}")
    
    def send_data(self, 
                  data: Union[str, bytes, Path],
                  recipient_public_key: Optional[bytes] = None,
                  compress: bool = True,
                  encrypt: bool = True) -> bool:
        """
        Send data via ultrasonic communication.
        
        Args:
            data: Data to send (string, bytes, or file path)
            recipient_public_key: RSA public key for encryption
            compress: Whether to compress the data
            encrypt: Whether to encrypt the data
            
        Returns:
            True if transmission was successful
        """
        try:
            # Load data if it's a file path
            if isinstance(data, (str, Path)):
                data_path = Path(data)
                if data_path.exists():
                    with open(data_path, 'rb') as f:
                        data = f.read()
                else:
                    data = str(data).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
            
            logger.info(f"Preparing to send {len(data)} bytes")
            
            # Compression
            if compress:
                data = self.compressor.compress(data)
                logger.info(f"Compressed to {len(data)} bytes")
            
            # Encryption
            if encrypt and recipient_public_key:
                data = self.crypto.encrypt(data, recipient_public_key)
                logger.info(f"Encrypted to {len(data)} bytes")
            
            # Modulation
            waveform = self.modulator.modulate(data)
            logger.info(f"Modulated to {len(waveform)} samples")
            
            # Transmission
            success = self.audio.transmit(waveform)
            
            if success:
                logger.info("Data transmission completed successfully")
            else:
                logger.error("Data transmission failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False
    
    def send_file(self, 
                  file_path: Union[str, Path],
                  recipient_public_key: Optional[bytes] = None) -> bool:
        """
        Send a file via ultrasonic communication.
        
        Args:
            file_path: Path to the file to send
            recipient_public_key: RSA public key for encryption
            
        Returns:
            True if transmission was successful
        """
        return self.send_data(file_path, recipient_public_key)
    
    def send_text(self, 
                  text: str,
                  recipient_public_key: Optional[bytes] = None) -> bool:
        """
        Send text via ultrasonic communication.
        
        Args:
            text: Text to send
            recipient_public_key: RSA public key for encryption
            
        Returns:
            True if transmission was successful
        """
        return self.send_data(text, recipient_public_key)


class SonicLinkReceiver:
    """
    Main class for receiving data via ultrasonic communication.
    
    Handles the complete pipeline: reception -> demodulation -> decryption -> decompression
    """
    
    def __init__(self, 
                 freq_range: FrequencyRange = None,
                 config: Config = None):
        """
        Initialize the SonicLink receiver.
        
        Args:
            freq_range: Frequency range for reception (default: 18-22 kHz)
            config: Configuration object
        """
        self.config = config or Config()
        self.freq_range = freq_range or FrequencyRange(18000, 22000)
        
        # Initialize components
        self.compressor = HuffmanCompressor()
        self.crypto = CryptoManager()
        self.demodulator = OFDMDemodulator(
            freq_range=self.freq_range,
            config=self.config
        )
        self.audio = AudioManager(config=self.config)
        
        logger.info(f"SonicLinkReceiver initialized with freq_range={self.freq_range}")
    
    def receive_data(self, 
                     timeout: float = 30.0,
                     private_key: Optional[bytes] = None,
                     decompress: bool = True,
                     decrypt: bool = True) -> Optional[bytes]:
        """
        Receive data via ultrasonic communication.
        
        Args:
            timeout: Timeout in seconds for reception
            private_key: RSA private key for decryption
            decompress: Whether to decompress the data
            decrypt: Whether to decrypt the data
            
        Returns:
            Received data as bytes, or None if reception failed
        """
        try:
            logger.info(f"Starting data reception (timeout: {timeout}s)")
            
            # Reception
            audio_data = self.audio.receive(timeout=timeout)
            if audio_data is None:
                logger.warning("No audio data received within timeout")
                return None
            
            logger.info(f"Received {len(audio_data)} audio samples")
            
            # Demodulation
            data = self.demodulator.demodulate(audio_data)
            if data is None:
                logger.error("Failed to demodulate audio data")
                return None
            
            logger.info(f"Demodulated to {len(data)} bytes")
            
            # Decryption
            if decrypt and private_key:
                data = self.crypto.decrypt(data, private_key)
                if data is None:
                    logger.error("Failed to decrypt data")
                    return None
                logger.info(f"Decrypted to {len(data)} bytes")
            
            # Decompression
            if decompress:
                data = self.compressor.decompress(data)
                if data is None:
                    logger.error("Failed to decompress data")
                    return None
                logger.info(f"Decompressed to {len(data)} bytes")
            
            logger.info("Data reception completed successfully")
            return data
            
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            return None
    
    def receive_to_file(self, 
                        output_path: Union[str, Path],
                        timeout: float = 30.0,
                        private_key: Optional[bytes] = None) -> bool:
        """
        Receive data and save to file.
        
        Args:
            output_path: Path to save the received data
            timeout: Timeout in seconds for reception
            private_key: RSA private key for decryption
            
        Returns:
            True if reception and save was successful
        """
        data = self.receive_data(timeout=timeout, private_key=private_key)
        if data is None:
            return False
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(data)
            
            logger.info(f"Data saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")
            return False
    
    def receive_text(self, 
                     timeout: float = 30.0,
                     private_key: Optional[bytes] = None) -> Optional[str]:
        """
        Receive text via ultrasonic communication.
        
        Args:
            timeout: Timeout in seconds for reception
            private_key: RSA private key for decryption
            
        Returns:
            Received text, or None if reception failed
        """
        data = self.receive_data(timeout=timeout, private_key=private_key)
        if data is None:
            return None
        
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            logger.error("Received data is not valid UTF-8 text")
            return None
    
    def start_listening(self, 
                       callback=None,
                       private_key: Optional[bytes] = None) -> bool:
        """
        Start continuous listening for data.
        
        Args:
            callback: Function to call when data is received
            private_key: RSA private key for decryption
            
        Returns:
            True if listening started successfully
        """
        def default_callback(data):
            print(f"Received {len(data)} bytes")
            try:
                text = data.decode('utf-8')
                print(f"Text: {text}")
            except UnicodeDecodeError:
                print("Binary data received")
        
        if callback is None:
            callback = default_callback
        
        try:
            logger.info("Starting continuous listening mode")
            return self.audio.start_listening(
                lambda audio_data: self._process_received_audio(audio_data, callback, private_key)
            )
        except Exception as e:
            logger.error(f"Error starting listening mode: {e}")
            return False
    
    def stop_listening(self):
        """Stop continuous listening."""
        self.audio.stop_listening()
        logger.info("Stopped listening mode")
    
    def _process_received_audio(self, audio_data, callback, private_key):
        """Process received audio data and call callback with result."""
        try:
            data = self.receive_data(private_key=private_key)
            if data is not None:
                callback(data)
        except Exception as e:
            logger.error(f"Error processing received audio: {e}") 