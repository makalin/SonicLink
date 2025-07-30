"""
Comprehensive test suite for SonicLink.
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import SonicLink components
from soniclink.compression import HuffmanCompressor
from soniclink.encryption import CryptoManager
from soniclink.modulation import OFDMModulator, OFDMDemodulator
from soniclink.audio import AudioManager
from soniclink.utils import FrequencyRange, Config, setup_logging
from soniclink.core import SonicLinkSender, SonicLinkReceiver


class TestHuffmanCompression:
    """Test Huffman compression functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.compressor = HuffmanCompressor()
    
    def test_compress_empty_data(self):
        """Test compression of empty data."""
        data = b''
        compressed = self.compressor.compress(data)
        assert compressed == b''
    
    def test_compress_simple_text(self):
        """Test compression of simple text."""
        data = b"Hello, World!"
        compressed = self.compressor.compress(data)
        
        # Compressed data should be different from original
        assert compressed != data
        
        # Should be able to decompress
        decompressed = self.compressor.decompress(compressed)
        assert decompressed == data
    
    def test_compress_repeated_data(self):
        """Test compression of data with repeated patterns."""
        data = b"AAAAABBBBBCCCCC" * 100
        compressed = self.compressor.compress(data)
        
        # Should be significantly smaller
        assert len(compressed) < len(data)
        
        # Should decompress correctly
        decompressed = self.compressor.decompress(compressed)
        assert decompressed == data
    
    def test_compress_large_data(self):
        """Test compression of large data."""
        # Generate random data
        data = np.random.bytes(10000)
        compressed = self.compressor.compress(data)
        
        # Should decompress correctly
        decompressed = self.compressor.decompress(compressed)
        assert decompressed == data
    
    def test_compression_stats(self):
        """Test compression statistics."""
        data = b"Test data for compression"
        compressed = self.compressor.compress(data)
        
        stats = self.compressor.get_stats()
        assert stats['original_size'] == len(data)
        assert stats['compressed_size'] == len(compressed)
        assert stats['compression_ratio'] > 0


class TestCryptoManager:
    """Test cryptographic functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.crypto = CryptoManager()
    
    def test_generate_key_pair(self):
        """Test RSA key pair generation."""
        private_key, public_key = self.crypto.generate_key_pair()
        
        assert len(private_key) > 0
        assert len(public_key) > 0
        assert private_key != public_key
    
    def test_save_load_keys(self):
        """Test saving and loading keys."""
        private_key, public_key = self.crypto.generate_key_pair()
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            private_path = f.name
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            public_path = f.name
        
        try:
            # Save keys
            self.crypto.save_key_pair(private_key, public_key, private_path, public_path)
            
            # Load keys
            loaded_private = self.crypto.load_private_key(private_path)
            loaded_public = self.crypto.load_public_key(public_path)
            
            assert loaded_private == private_key
            assert loaded_public == public_key
            
        finally:
            # Cleanup
            os.unlink(private_path)
            os.unlink(public_path)
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        private_key, public_key = self.crypto.generate_key_pair()
        data = b"Secret message for encryption test"
        
        # Encrypt
        encrypted = self.crypto.encrypt(data, public_key)
        assert encrypted != data
        assert len(encrypted) > len(data)
        
        # Decrypt
        decrypted = self.crypto.decrypt(encrypted, private_key)
        assert decrypted == data
    
    def test_symmetric_encryption(self):
        """Test symmetric encryption."""
        data = b"Test data for symmetric encryption"
        
        # Encrypt
        encrypted, key = self.crypto.encrypt_symmetric(data)
        assert encrypted != data
        
        # Decrypt
        decrypted = self.crypto.decrypt_symmetric(encrypted, key)
        assert decrypted == data
    
    def test_hash_function(self):
        """Test hash function."""
        data1 = b"Test data"
        data2 = b"Test data"
        data3 = b"Different data"
        
        hash1 = self.crypto.hash_data(data1)
        hash2 = self.crypto.hash_data(data2)
        hash3 = self.crypto.hash_data(data3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # SHA-256 produces 32 bytes


class TestOFDMModulation:
    """Test OFDM modulation and demodulation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.freq_range = FrequencyRange(18000, 22000)
        self.config = Config()
        self.modulator = OFDMModulator(self.freq_range, config=self.config)
        self.demodulator = OFDMDemodulator(self.freq_range, config=self.config)
    
    def test_modulator_initialization(self):
        """Test modulator initialization."""
        assert self.modulator.carrier_count == 64
        assert self.modulator.cyclic_prefix_length == 16
        assert len(self.modulator.carrier_freqs) == 64
        assert self.modulator.carrier_freqs[0] == 18000
        assert self.modulator.carrier_freqs[-1] == 22000
    
    def test_qam_constellation(self):
        """Test QAM constellation creation."""
        constellation = self.modulator.qam_constellation
        assert len(constellation) == 64
        
        # Check that constellation points are complex numbers
        for point in constellation:
            assert isinstance(point, complex)
    
    def test_modulation_demodulation(self):
        """Test complete modulation and demodulation cycle."""
        # Small test data
        data = b"Test data for OFDM"
        
        # Modulate
        waveform = self.modulator.modulate(data)
        assert len(waveform) > 0
        assert isinstance(waveform, np.ndarray)
        
        # Demodulate
        demodulated = self.demodulator.demodulate(waveform)
        assert demodulated == data
    
    def test_modulation_large_data(self):
        """Test modulation of larger data."""
        # Generate larger test data
        data = b"Large test data " * 100
        
        # Modulate
        waveform = self.modulator.modulate(data)
        assert len(waveform) > 0
        
        # Demodulate
        demodulated = self.demodulator.demodulate(waveform)
        assert demodulated == data
    
    def test_marker_detection(self):
        """Test start/end marker detection."""
        data = b"Test data"
        waveform = self.modulator.modulate(data)
        
        # Check that waveform has markers (should be longer than just data)
        assert len(waveform) > len(data) * 100  # Rough estimate


class TestAudioManager:
    """Test audio management functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Config()
        self.audio = AudioManager(self.config)
    
    def teardown_method(self):
        """Cleanup after tests."""
        self.audio.cleanup()
    
    def test_audio_initialization(self):
        """Test audio manager initialization."""
        assert self.audio.sample_rate == 48000
        assert self.audio.chunk_size == 1024
        assert self.audio.channels == 1
    
    def test_get_audio_devices(self):
        """Test getting audio devices."""
        devices = self.audio.get_audio_devices()
        
        assert 'input' in devices
        assert 'output' in devices
        assert isinstance(devices['input'], list)
        assert isinstance(devices['output'], list)
    
    def test_normalize_audio(self):
        """Test audio normalization."""
        # Create test waveform
        waveform = np.array([0.5, -0.3, 0.8, -0.9, 0.1])
        
        normalized = self.audio._normalize_audio(waveform)
        
        # Should not clip
        assert np.max(np.abs(normalized)) <= 0.8
        
        # Should preserve relative amplitudes
        assert np.allclose(normalized / np.max(np.abs(normalized)), 
                          waveform / np.max(np.abs(waveform)))
    
    def test_calculate_energy(self):
        """Test energy calculation."""
        # Create test audio data
        audio_data = b'\x00\x00\x7F\x7F\x00\x00'  # Some audio samples
        
        energy = self.audio._calculate_energy(audio_data)
        assert energy >= 0
    
    @patch('pyaudio.PyAudio')
    def test_transmit_mock(self, mock_pyaudio):
        """Test transmission with mocked PyAudio."""
        # Mock PyAudio
        mock_stream = Mock()
        mock_pyaudio.return_value.open.return_value = mock_stream
        
        # Create test waveform
        waveform = np.sin(2 * np.pi * 1000 * np.arange(1000) / 48000)
        
        # Test transmission
        success = self.audio.transmit(waveform)
        assert success
    
    @patch('pyaudio.PyAudio')
    def test_receive_mock(self, mock_pyaudio):
        """Test reception with mocked PyAudio."""
        # Mock PyAudio
        mock_stream = Mock()
        mock_stream.read.return_value = b'\x00\x00' * 512  # Mock audio data
        mock_pyaudio.return_value.open.return_value = mock_stream
        
        # Test reception
        audio_data = self.audio.receive(timeout=1.0)
        assert audio_data is not None


class TestSonicLinkCore:
    """Test core SonicLink functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Config()
        self.freq_range = FrequencyRange(18000, 22000)
        self.sender = SonicLinkSender(self.freq_range, config=self.config)
        self.receiver = SonicLinkReceiver(self.freq_range, config=self.config)
    
    def test_sender_initialization(self):
        """Test sender initialization."""
        assert self.sender.freq_range == self.freq_range
        assert self.sender.bitrate == 80000
        assert self.sender.config == self.config
    
    def test_receiver_initialization(self):
        """Test receiver initialization."""
        assert self.receiver.freq_range == self.freq_range
        assert self.receiver.config == self.config
    
    def test_send_text(self):
        """Test text sending."""
        text = "Hello, SonicLink!"
        
        # Mock the audio transmission
        with patch.object(self.sender.audio, 'transmit', return_value=True):
            success = self.sender.send_text(text)
            assert success
    
    def test_send_file(self):
        """Test file sending."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test file content")
            file_path = f.name
        
        try:
            # Mock the audio transmission
            with patch.object(self.sender.audio, 'transmit', return_value=True):
                success = self.sender.send_file(file_path)
                assert success
        finally:
            os.unlink(file_path)
    
    def test_receive_text(self):
        """Test text receiving."""
        # Mock the audio reception
        with patch.object(self.receiver.audio, 'receive', return_value=np.array([0.1, 0.2, 0.3])):
            with patch.object(self.receiver.demodulator, 'demodulate', return_value=b"Test message"):
                text = self.receiver.receive_text()
                assert text == "Test message"


class TestUtils:
    """Test utility functions."""
    
    def test_frequency_range(self):
        """Test FrequencyRange class."""
        freq_range = FrequencyRange(18000, 22000)
        
        assert freq_range.min_freq == 18000
        assert freq_range.max_freq == 22000
        assert freq_range.bandwidth == 4000
        assert freq_range.center_freq == 20000
        assert str(freq_range) == "18000-22000 Hz"
    
    def test_frequency_range_validation(self):
        """Test FrequencyRange validation."""
        # Should raise error for invalid range
        with pytest.raises(ValueError):
            FrequencyRange(22000, 18000)
        
        # Should raise error for negative frequencies
        with pytest.raises(ValueError):
            FrequencyRange(-1000, 1000)
    
    def test_config(self):
        """Test Config class."""
        config = Config()
        
        assert config.sample_rate == 48000
        assert config.chunk_size == 1024
        assert config.encryption_enabled == True
        assert config.compression_enabled == True
    
    def test_config_serialization(self):
        """Test Config serialization."""
        config = Config()
        
        # Convert to dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'sample_rate' in config_dict
        
        # Convert back to config
        new_config = Config.from_dict(config_dict)
        assert new_config.sample_rate == config.sample_rate
        assert new_config.chunk_size == config.chunk_size
    
    def test_config_save_load(self):
        """Test Config save/load functionality."""
        config = Config()
        config.sample_rate = 44100
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            config_path = f.name
        
        try:
            # Save config
            config.save(config_path)
            
            # Load config
            loaded_config = Config.load(config_path)
            assert loaded_config.sample_rate == 44100
        finally:
            os.unlink(config_path)


class TestIntegration:
    """Integration tests for complete SonicLink workflow."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Config()
        self.freq_range = FrequencyRange(18000, 22000)
    
    def test_complete_workflow(self):
        """Test complete SonicLink workflow."""
        # Generate keys
        crypto = CryptoManager()
        private_key, public_key = crypto.generate_key_pair()
        
        # Create sender and receiver
        sender = SonicLinkSender(self.freq_range, config=self.config)
        receiver = SonicLinkReceiver(self.freq_range, config=self.config)
        
        # Test data
        test_data = b"Integration test data"
        
        # Mock audio transmission and reception
        with patch.object(sender.audio, 'transmit', return_value=True):
            with patch.object(receiver.audio, 'receive', return_value=np.array([0.1, 0.2, 0.3])):
                with patch.object(receiver.demodulator, 'demodulate', return_value=test_data):
                    # Send data
                    success = sender.send_data(test_data, public_key)
                    assert success
                    
                    # Receive data
                    received = receiver.receive_data(private_key=private_key)
                    assert received == test_data


if __name__ == "__main__":
    pytest.main([__file__]) 