"""
Audio handling module for SonicLink using PyAudio.
"""

import pyaudio
import numpy as np
import logging
import threading
import time
from typing import Optional, Callable
from queue import Queue

from .utils import Config

logger = logging.getLogger(__name__)


class AudioManager:
    """
    Audio manager for SonicLink using PyAudio.
    
    Handles real-time audio input/output for ultrasonic communication.
    """
    
    def __init__(self, config: Config = None):
        """
        Initialize audio manager.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.sample_rate = self.config.sample_rate
        self.chunk_size = self.config.chunk_size
        self.channels = 1  # Mono audio
        
        # PyAudio instance
        self.pyaudio = pyaudio.PyAudio()
        
        # Audio streams
        self.input_stream = None
        self.output_stream = None
        
        # Listening mode
        self.is_listening = False
        self.listening_thread = None
        self.callback_queue = Queue()
        
        # Audio processing
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
        logger.info(f"Audio manager initialized: {self.sample_rate} Hz, "
                   f"{self.channels} channels, chunk size {self.chunk_size}")
    
    def __del__(self):
        """Cleanup audio resources."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            self.stop_listening()
            
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
            
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
            
            if self.pyaudio:
                self.pyaudio.terminate()
                
            logger.info("Audio resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during audio cleanup: {e}")
    
    def get_audio_devices(self) -> dict:
        """
        Get available audio devices.
        
        Returns:
            Dictionary of available input and output devices
        """
        devices = {
            'input': [],
            'output': []
        }
        
        try:
            for i in range(self.pyaudio.get_device_count()):
                device_info = self.pyaudio.get_device_info_by_index(i)
                
                if device_info['maxInputChannels'] > 0:
                    devices['input'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate'])
                    })
                
                if device_info['maxOutputChannels'] > 0:
                    devices['output'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxOutputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate'])
                    })
            
            logger.info(f"Found {len(devices['input'])} input devices, "
                       f"{len(devices['output'])} output devices")
            
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
        
        return devices
    
    def transmit(self, waveform: np.ndarray, device_index: Optional[int] = None) -> bool:
        """
        Transmit audio waveform through speakers.
        
        Args:
            waveform: Audio waveform to transmit
            device_index: Output device index (None for default)
            
        Returns:
            True if transmission was successful
        """
        try:
            # Normalize waveform
            waveform = self._normalize_audio(waveform)
            
            # Convert to proper format
            audio_data = (waveform * 32767).astype(np.int16).tobytes()
            
            # Open output stream
            self.output_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Transmit audio
            logger.info(f"Starting transmission of {len(waveform)} samples")
            
            # Send audio in chunks
            for i in range(0, len(audio_data), self.chunk_size * 2):  # 2 bytes per sample
                chunk = audio_data[i:i + self.chunk_size * 2]
                if chunk:
                    self.output_stream.write(chunk)
            
            # Close stream
            self.output_stream.stop_stream()
            self.output_stream.close()
            self.output_stream = None
            
            logger.info("Transmission completed")
            return True
            
        except Exception as e:
            logger.error(f"Transmission failed: {e}")
            if self.output_stream:
                self.output_stream.close()
                self.output_stream = None
            return False
    
    def receive(self, timeout: float = 30.0, device_index: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Receive audio from microphone.
        
        Args:
            timeout: Timeout in seconds
            device_index: Input device index (None for default)
            
        Returns:
            Received audio data as numpy array, or None if reception failed
        """
        try:
            # Open input stream
            self.input_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info(f"Starting reception (timeout: {timeout}s)")
            
            # Receive audio
            audio_frames = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_frames.append(data)
                    
                    # Check for end marker (simple energy-based detection)
                    if len(audio_frames) > 10:  # Need some data first
                        recent_energy = self._calculate_energy(data)
                        if recent_energy < 100:  # Low energy might indicate end
                            # Wait a bit more to confirm
                            time.sleep(0.1)
                            data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                            if self._calculate_energy(data) < 100:
                                break
                
                except Exception as e:
                    logger.warning(f"Error reading audio chunk: {e}")
                    break
            
            # Close stream
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
            
            if not audio_frames:
                logger.warning("No audio data received")
                return None
            
            # Convert frames to numpy array
            audio_data = b''.join(audio_frames)
            waveform = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            logger.info(f"Reception completed: {len(waveform)} samples")
            return waveform
            
        except Exception as e:
            logger.error(f"Reception failed: {e}")
            if self.input_stream:
                self.input_stream.close()
                self.input_stream = None
            return None
    
    def start_listening(self, callback: Callable[[np.ndarray], None], 
                       device_index: Optional[int] = None) -> bool:
        """
        Start continuous listening mode.
        
        Args:
            callback: Function to call when audio is received
            device_index: Input device index (None for default)
            
        Returns:
            True if listening started successfully
        """
        if self.is_listening:
            logger.warning("Already listening")
            return False
        
        try:
            # Open input stream
            self.input_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            self.callback_queue.put(callback)
            
            # Start listening thread
            self.listening_thread = threading.Thread(target=self._listening_worker)
            self.listening_thread.daemon = True
            self.listening_thread.start()
            
            logger.info("Started continuous listening mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            return False
    
    def stop_listening(self):
        """Stop continuous listening mode."""
        if not self.is_listening:
            return
        
        try:
            self.is_listening = False
            
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            if self.listening_thread:
                self.listening_thread.join(timeout=1.0)
                self.listening_thread = None
            
            # Clear callback queue
            while not self.callback_queue.empty():
                try:
                    self.callback_queue.get_nowait()
                except:
                    pass
            
            logger.info("Stopped continuous listening mode")
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for continuous audio input."""
        if self.is_listening:
            # Convert to numpy array
            audio_chunk = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Add to buffer
            with self.buffer_lock:
                self.audio_buffer.append(audio_chunk)
                
                # Keep only recent audio (last 5 seconds)
                total_samples = sum(len(chunk) for chunk in self.audio_buffer)
                max_samples = int(5 * self.sample_rate)
                
                while total_samples > max_samples and len(self.audio_buffer) > 1:
                    removed_chunk = self.audio_buffer.pop(0)
                    total_samples -= len(removed_chunk)
        
        return (in_data, pyaudio.paContinue)
    
    def _listening_worker(self):
        """Worker thread for continuous listening."""
        while self.is_listening:
            try:
                # Get callback
                callback = self.callback_queue.get(timeout=0.1)
                
                # Check for audio data
                with self.buffer_lock:
                    if self.audio_buffer:
                        # Combine recent audio chunks
                        audio_data = np.concatenate(self.audio_buffer)
                        self.audio_buffer.clear()
                        
                        # Call callback
                        try:
                            callback(audio_data)
                        except Exception as e:
                            logger.error(f"Error in audio callback: {e}")
                
            except Exception as e:
                if self.is_listening:  # Only log if still listening
                    logger.error(f"Error in listening worker: {e}")
    
    def _normalize_audio(self, waveform: np.ndarray) -> np.ndarray:
        """Normalize audio waveform to prevent clipping."""
        max_val = np.max(np.abs(waveform))
        if max_val > 0:
            # Normalize to 0.8 to leave some headroom
            waveform = waveform * 0.8 / max_val
        return waveform
    
    def _calculate_energy(self, audio_data: bytes) -> float:
        """Calculate energy of audio chunk."""
        try:
            samples = np.frombuffer(audio_data, dtype=np.int16)
            return np.mean(samples ** 2)
        except:
            return 0.0
    
    def record_test_tone(self, duration: float = 1.0, frequency: float = 1000.0) -> Optional[np.ndarray]:
        """
        Record a test tone for calibration.
        
        Args:
            duration: Recording duration in seconds
            frequency: Test tone frequency in Hz
            
        Returns:
            Recorded audio data, or None if recording failed
        """
        try:
            # Generate test tone
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            test_tone = np.sin(2 * np.pi * frequency * t)
            
            # Transmit test tone
            if not self.transmit(test_tone):
                return None
            
            # Wait a moment
            time.sleep(0.1)
            
            # Record response
            return self.receive(timeout=duration + 1.0)
            
        except Exception as e:
            logger.error(f"Test tone recording failed: {e}")
            return None
    
    def get_audio_levels(self, duration: float = 1.0) -> dict:
        """
        Get current audio input/output levels.
        
        Args:
            duration: Measurement duration in seconds
            
        Returns:
            Dictionary with input and output levels
        """
        levels = {
            'input_level': 0.0,
            'output_level': 0.0
        }
        
        try:
            # Measure input level
            audio_data = self.receive(timeout=duration)
            if audio_data is not None:
                levels['input_level'] = float(np.sqrt(np.mean(audio_data ** 2)))
            
            # Measure output level (would need a loopback test)
            # For now, just return input level
            levels['output_level'] = levels['input_level']
            
        except Exception as e:
            logger.error(f"Error measuring audio levels: {e}")
        
        return levels 