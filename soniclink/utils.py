"""
Utility classes and functions for SonicLink.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class FrequencyRange:
    """Frequency range for ultrasonic communication."""
    
    min_freq: float
    max_freq: float
    
    def __post_init__(self):
        """Validate frequency range."""
        if self.min_freq >= self.max_freq:
            raise ValueError("min_freq must be less than max_freq")
        
        if self.min_freq < 0 or self.max_freq < 0:
            raise ValueError("Frequencies must be positive")
    
    def __str__(self):
        return f"{self.min_freq}-{self.max_freq} Hz"
    
    def __repr__(self):
        return f"FrequencyRange({self.min_freq}, {self.max_freq})"
    
    @property
    def bandwidth(self) -> float:
        """Get frequency bandwidth."""
        return self.max_freq - self.min_freq
    
    @property
    def center_freq(self) -> float:
        """Get center frequency."""
        return (self.min_freq + self.max_freq) / 2


@dataclass
class Config:
    """Configuration for SonicLink."""
    
    # Audio settings
    sample_rate: int = 48000
    chunk_size: int = 1024
    channels: int = 1
    
    # Communication settings
    default_bitrate: int = 80000
    default_freq_range: FrequencyRange = None
    
    # Security settings
    encryption_enabled: bool = True
    compression_enabled: bool = True
    
    # Error correction settings
    reed_solomon_enabled: bool = True
    rs_n: int = 255
    rs_k: int = 223
    
    # OFDM settings
    ofdm_carriers: int = 64
    ofdm_cyclic_prefix: int = 16
    ofdm_symbol_duration: float = 0.01
    
    # Audio processing settings
    noise_filter_enabled: bool = True
    adaptive_gain: bool = True
    max_gain: float = 10.0
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.default_freq_range is None:
            self.default_freq_range = FrequencyRange(18000, 22000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'sample_rate': self.sample_rate,
            'chunk_size': self.chunk_size,
            'channels': self.channels,
            'default_bitrate': self.default_bitrate,
            'default_freq_range': {
                'min_freq': self.default_freq_range.min_freq,
                'max_freq': self.default_freq_range.max_freq
            },
            'encryption_enabled': self.encryption_enabled,
            'compression_enabled': self.compression_enabled,
            'reed_solomon_enabled': self.reed_solomon_enabled,
            'rs_n': self.rs_n,
            'rs_k': self.rs_k,
            'ofdm_carriers': self.ofdm_carriers,
            'ofdm_cyclic_prefix': self.ofdm_cyclic_prefix,
            'ofdm_symbol_duration': self.ofdm_symbol_duration,
            'noise_filter_enabled': self.noise_filter_enabled,
            'adaptive_gain': self.adaptive_gain,
            'max_gain': self.max_gain,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Extract frequency range
        freq_range_data = data.get('default_freq_range', {})
        freq_range = FrequencyRange(
            freq_range_data.get('min_freq', 18000),
            freq_range_data.get('max_freq', 22000)
        )
        
        return cls(
            sample_rate=data.get('sample_rate', 48000),
            chunk_size=data.get('chunk_size', 1024),
            channels=data.get('channels', 1),
            default_bitrate=data.get('default_bitrate', 80000),
            default_freq_range=freq_range,
            encryption_enabled=data.get('encryption_enabled', True),
            compression_enabled=data.get('compression_enabled', True),
            reed_solomon_enabled=data.get('reed_solomon_enabled', True),
            rs_n=data.get('rs_n', 255),
            rs_k=data.get('rs_k', 223),
            ofdm_carriers=data.get('ofdm_carriers', 64),
            ofdm_cyclic_prefix=data.get('ofdm_cyclic_prefix', 16),
            ofdm_symbol_duration=data.get('ofdm_symbol_duration', 0.01),
            noise_filter_enabled=data.get('noise_filter_enabled', True),
            adaptive_gain=data.get('adaptive_gain', True),
            max_gain=data.get('max_gain', 10.0),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file')
        )
    
    def save(self, file_path: str):
        """Save config to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save config: {e}")
    
    @classmethod
    def load(cls, file_path: str) -> 'Config':
        """Load config from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")


def setup_logging(config: Config):
    """Setup logging configuration."""
    log_config = {
        'level': getattr(logging, config.log_level.upper()),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': []
    }
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_config['format']))
    log_config['handlers'].append(console_handler)
    
    # File handler (if specified)
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter(log_config['format']))
        log_config['handlers'].append(file_handler)
    
    # Configure logging
    logging.basicConfig(**log_config)


def calculate_optimal_bitrate(freq_range: FrequencyRange, snr_db: float = 20.0) -> int:
    """
    Calculate optimal bitrate based on frequency range and SNR.
    
    Args:
        freq_range: Frequency range for communication
        snr_db: Signal-to-noise ratio in dB
        
    Returns:
        Optimal bitrate in bits per second
    """
    # Shannon capacity formula: C = B * log2(1 + SNR)
    bandwidth = freq_range.bandwidth
    snr_linear = 10 ** (snr_db / 10)
    
    # Theoretical capacity
    capacity = bandwidth * np.log2(1 + snr_linear)
    
    # Apply practical efficiency factor (typically 0.6-0.8)
    efficiency = 0.7
    practical_bitrate = int(capacity * efficiency)
    
    # Ensure reasonable limits
    min_bitrate = 1000   # 1 kbps minimum
    max_bitrate = 200000 # 200 kbps maximum
    
    return max(min_bitrate, min(practical_bitrate, max_bitrate))


def estimate_transmission_time(data_size: int, bitrate: int) -> float:
    """
    Estimate transmission time for given data size and bitrate.
    
    Args:
        data_size: Data size in bytes
        bitrate: Bitrate in bits per second
        
    Returns:
        Estimated transmission time in seconds
    """
    bits = data_size * 8
    return bits / bitrate


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


# Import numpy for calculations
import numpy as np 