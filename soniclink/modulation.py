"""
OFDM modulation and demodulation for SonicLink.
"""

import numpy as np
import logging
from typing import Optional, List, Tuple
from scipy import signal
from reedsolo import RSCodec

from .utils import FrequencyRange, Config

logger = logging.getLogger(__name__)


class OFDMModulator:
    """
    OFDM modulator with 64-QAM for SonicLink.
    
    Converts digital data to analog waveform using OFDM modulation
    with 64-QAM constellation mapping.
    """
    
    def __init__(self, 
                 freq_range: FrequencyRange,
                 bitrate: int = 80000,
                 config: Config = None):
        """
        Initialize OFDM modulator.
        
        Args:
            freq_range: Frequency range for transmission
            bitrate: Target bitrate in bits per second
            config: Configuration object
        """
        self.config = config or Config()
        self.freq_range = freq_range
        self.bitrate = bitrate
        
        # OFDM parameters
        self.sample_rate = self.config.sample_rate
        self.carrier_count = 64  # Number of OFDM carriers
        self.cyclic_prefix_length = 16  # Cyclic prefix length
        self.symbol_duration = 0.01  # Symbol duration in seconds
        
        # Calculate carrier frequencies
        self.carrier_freqs = np.linspace(
            freq_range.min_freq, 
            freq_range.max_freq, 
            self.carrier_count
        )
        
        # 64-QAM constellation mapping
        self.qam_constellation = self._create_qam_constellation()
        
        # Error correction
        self.rs_codec = RSCodec(255, 223)  # Reed-Solomon code
        
        logger.info(f"OFDM modulator initialized: {self.carrier_count} carriers, "
                   f"{self.bitrate} bps, freq range {freq_range}")
    
    def modulate(self, data: bytes) -> np.ndarray:
        """
        Modulate data using OFDM with 64-QAM.
        
        Args:
            data: Data to modulate
            
        Returns:
            Modulated waveform as numpy array
        """
        try:
            # Add error correction
            encoded_data = self.rs_codec.encode(data)
            
            # Convert to bits
            bits = self._bytes_to_bits(encoded_data)
            
            # Pad bits to fit OFDM symbols
            bits_per_symbol = self.carrier_count * 6  # 6 bits per carrier (64-QAM)
            padding_length = (bits_per_symbol - len(bits) % bits_per_symbol) % bits_per_symbol
            bits.extend([0] * padding_length)
            
            # Group bits into symbols
            symbols = []
            for i in range(0, len(bits), bits_per_symbol):
                symbol_bits = bits[i:i+bits_per_symbol]
                symbol = self._bits_to_qam_symbols(symbol_bits)
                symbols.append(symbol)
            
            # Generate OFDM waveform
            waveform = self._generate_ofdm_waveform(symbols)
            
            # Add start/end markers
            waveform = self._add_markers(waveform)
            
            logger.info(f"Modulated {len(data)} bytes to {len(waveform)} samples")
            return waveform
            
        except Exception as e:
            logger.error(f"Modulation failed: {e}")
            raise
    
    def _create_qam_constellation(self) -> np.ndarray:
        """Create 64-QAM constellation points."""
        # Create 8x8 grid of constellation points
        real_values = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / np.sqrt(42)
        imag_values = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / np.sqrt(42)
        
        constellation = []
        for real in real_values:
            for imag in imag_values:
                constellation.append(complex(real, imag))
        
        return np.array(constellation)
    
    def _bytes_to_bits(self, data: bytes) -> List[int]:
        """Convert bytes to list of bits."""
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits
    
    def _bits_to_qam_symbols(self, bits: List[int]) -> np.ndarray:
        """Convert bits to QAM symbols."""
        symbols = []
        for i in range(0, len(bits), 6):
            if i + 6 <= len(bits):
                # Take 6 bits for 64-QAM
                bit_group = bits[i:i+6]
                symbol_index = sum(bit * (2 ** (5 - j)) for j, bit in enumerate(bit_group))
                symbols.append(self.qam_constellation[symbol_index])
        
        return np.array(symbols)
    
    def _generate_ofdm_waveform(self, symbols: List[np.ndarray]) -> np.ndarray:
        """Generate OFDM waveform from symbols."""
        samples_per_symbol = int(self.symbol_duration * self.sample_rate)
        total_samples = len(symbols) * samples_per_symbol
        
        waveform = np.zeros(total_samples, dtype=np.float32)
        
        for i, symbol in enumerate(symbols):
            # Generate OFDM symbol
            symbol_samples = self._generate_ofdm_symbol(symbol, samples_per_symbol)
            
            # Add to waveform
            start_idx = i * samples_per_symbol
            end_idx = start_idx + len(symbol_samples)
            waveform[start_idx:end_idx] = symbol_samples
        
        return waveform
    
    def _generate_ofdm_symbol(self, symbol: np.ndarray, samples_per_symbol: int) -> np.ndarray:
        """Generate single OFDM symbol."""
        # IFFT to convert frequency domain to time domain
        ifft_input = np.zeros(self.carrier_count, dtype=complex)
        ifft_input[:len(symbol)] = symbol
        
        # Perform IFFT
        time_domain = np.fft.ifft(ifft_input)
        
        # Add cyclic prefix
        cyclic_prefix = time_domain[-self.cyclic_prefix_length:]
        symbol_with_prefix = np.concatenate([cyclic_prefix, time_domain])
        
        # Convert to real signal
        real_symbol = np.real(symbol_with_prefix)
        
        # Resample to desired length
        if len(real_symbol) != samples_per_symbol:
            real_symbol = signal.resample(real_symbol, samples_per_symbol)
        
        return real_symbol
    
    def _add_markers(self, waveform: np.ndarray) -> np.ndarray:
        """Add start and end markers to waveform."""
        # Start marker (17.5 kHz tone)
        start_freq = 17500
        start_duration = 0.1  # 100ms
        start_samples = int(start_duration * self.sample_rate)
        start_marker = np.sin(2 * np.pi * start_freq * np.arange(start_samples) / self.sample_rate)
        
        # End marker (17.5 kHz tone with different phase)
        end_marker = -start_marker
        
        # Combine markers with waveform
        result = np.concatenate([start_marker, waveform, end_marker])
        
        return result


class OFDMDemodulator:
    """
    OFDM demodulator with 64-QAM for SonicLink.
    
    Converts analog waveform back to digital data using OFDM demodulation
    with 64-QAM constellation demapping.
    """
    
    def __init__(self, 
                 freq_range: FrequencyRange,
                 config: Config = None):
        """
        Initialize OFDM demodulator.
        
        Args:
            freq_range: Frequency range for reception
            config: Configuration object
        """
        self.config = config or Config()
        self.freq_range = freq_range
        
        # OFDM parameters (must match modulator)
        self.sample_rate = self.config.sample_rate
        self.carrier_count = 64
        self.cyclic_prefix_length = 16
        self.symbol_duration = 0.01
        
        # Calculate carrier frequencies
        self.carrier_freqs = np.linspace(
            freq_range.min_freq, 
            freq_range.max_freq, 
            self.carrier_count
        )
        
        # 64-QAM constellation mapping
        self.qam_constellation = self._create_qam_constellation()
        
        # Error correction
        self.rs_codec = RSCodec(255, 223)
        
        logger.info(f"OFDM demodulator initialized: {self.carrier_count} carriers, "
                   f"freq range {freq_range}")
    
    def demodulate(self, audio_data: np.ndarray) -> Optional[bytes]:
        """
        Demodulate audio data using OFDM with 64-QAM.
        
        Args:
            audio_data: Audio data to demodulate
            
        Returns:
            Demodulated data as bytes, or None if demodulation failed
        """
        try:
            # Detect and extract data portion
            data_portion = self._extract_data_portion(audio_data)
            if data_portion is None:
                return None
            
            # Synchronize and extract OFDM symbols
            symbols = self._extract_ofdm_symbols(data_portion)
            if not symbols:
                return None
            
            # Demodulate symbols to bits
            bits = self._demodulate_symbols(symbols)
            if not bits:
                return None
            
            # Convert bits to bytes
            data = self._bits_to_bytes(bits)
            if not data:
                return None
            
            # Error correction
            try:
                decoded_data = self.rs_codec.decode(data)
                logger.info(f"Demodulated {len(audio_data)} samples to {len(decoded_data)} bytes")
                return decoded_data
            except Exception as e:
                logger.warning(f"Error correction failed: {e}")
                return data
            
        except Exception as e:
            logger.error(f"Demodulation failed: {e}")
            return None
    
    def _create_qam_constellation(self) -> np.ndarray:
        """Create 64-QAM constellation points (same as modulator)."""
        real_values = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / np.sqrt(42)
        imag_values = np.array([-7, -5, -3, -1, 1, 3, 5, 7]) / np.sqrt(42)
        
        constellation = []
        for real in real_values:
            for imag in imag_values:
                constellation.append(complex(real, imag))
        
        return np.array(constellation)
    
    def _extract_data_portion(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Extract data portion between start and end markers."""
        # Detect start marker (17.5 kHz)
        start_freq = 17500
        start_duration = 0.1
        
        # Simple correlation-based detection
        marker_samples = int(start_duration * self.sample_rate)
        marker = np.sin(2 * np.pi * start_freq * np.arange(marker_samples) / self.sample_rate)
        
        # Find start marker
        correlation = np.correlate(audio_data, marker, mode='valid')
        start_idx = np.argmax(np.abs(correlation))
        
        if start_idx < 0:
            logger.warning("Start marker not found")
            return None
        
        # Find end marker (negative correlation)
        end_marker = -marker
        correlation = np.correlate(audio_data[start_idx:], end_marker, mode='valid')
        end_idx = np.argmax(np.abs(correlation))
        
        if end_idx < 0:
            logger.warning("End marker not found")
            return None
        
        # Extract data portion
        data_start = start_idx + marker_samples
        data_end = start_idx + end_idx
        
        if data_end <= data_start:
            logger.warning("Invalid data portion")
            return None
        
        return audio_data[data_start:data_end]
    
    def _extract_ofdm_symbols(self, data_portion: np.ndarray) -> List[np.ndarray]:
        """Extract OFDM symbols from data portion."""
        samples_per_symbol = int(self.symbol_duration * self.sample_rate)
        symbols = []
        
        for i in range(0, len(data_portion), samples_per_symbol):
            if i + samples_per_symbol <= len(data_portion):
                symbol_data = data_portion[i:i+samples_per_symbol]
                symbol = self._extract_ofdm_symbol(symbol_data)
                if symbol is not None:
                    symbols.append(symbol)
        
        return symbols
    
    def _extract_ofdm_symbol(self, symbol_data: np.ndarray) -> Optional[np.ndarray]:
        """Extract single OFDM symbol."""
        try:
            # Remove cyclic prefix
            symbol_without_prefix = symbol_data[self.cyclic_prefix_length:]
            
            # Perform FFT
            freq_domain = np.fft.fft(symbol_without_prefix)
            
            # Extract carrier symbols
            symbols = freq_domain[:self.carrier_count]
            
            return symbols
            
        except Exception as e:
            logger.warning(f"Failed to extract OFDM symbol: {e}")
            return None
    
    def _demodulate_symbols(self, symbols: List[np.ndarray]) -> List[int]:
        """Demodulate symbols to bits."""
        bits = []
        
        for symbol in symbols:
            symbol_bits = self._qam_symbols_to_bits(symbol)
            bits.extend(symbol_bits)
        
        return bits
    
    def _qam_symbols_to_bits(self, symbols: np.ndarray) -> List[int]:
        """Convert QAM symbols to bits."""
        bits = []
        
        for symbol in symbols:
            # Find closest constellation point
            distances = np.abs(self.qam_constellation - symbol)
            closest_idx = np.argmin(distances)
            
            # Convert index to 6 bits
            for i in range(6):
                bit = (closest_idx >> (5 - i)) & 1
                bits.append(bit)
        
        return bits
    
    def _bits_to_bytes(self, bits: List[int]) -> Optional[bytes]:
        """Convert bits to bytes."""
        if len(bits) % 8 != 0:
            logger.warning(f"Bit count {len(bits)} is not multiple of 8")
            return None
        
        bytes_data = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_val = sum(bit * (2 ** (7 - j)) for j, bit in enumerate(byte_bits))
            bytes_data.append(byte_val)
        
        return bytes(bytes_data) 