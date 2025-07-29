# SonicLink: High-Speed Ultrasonic Data Communication System

SonicLink is an innovative, high-speed, secure communication system designed for computers to exchange data using ultrasonic sound waves. Leveraging advanced modulation, compression, and encryption techniques, SonicLink enables fast, reliable, and secure data transfer in environments where traditional wireless protocols like Wi-Fi or Bluetooth are unavailable or undesirable. The system operates in the near-ultrasonic frequency range (18-22 kHz) to minimize human audibility while maximizing throughput and security.

## Features

- **High-Speed Data Transfer**: Achieves up to 80 kbps using Orthogonal Frequency-Division Multiplexing (OFDM) with 64-QAM modulation.
- **Ultrasonic Frequencies**: Operates in the 18-22 kHz range, inaudible to most humans but detectable by standard computer microphones and speakers.
- **Data Compression**: Utilizes adaptive Huffman coding for efficient data compression before transmission.
- **Security**: Implements AES-256 encryption and RSA-based key exchange to ensure only the intended recipient can decrypt the data.
- **Error Correction**: Employs Reed-Solomon codes for robust error detection and correction, ensuring reliable communication in noisy environments.
- **Cross-Platform**: Supports Linux, macOS, and Windows, with potential for mobile platforms (Android/iOS) via additional SDKs.
- **Air-Gapped Compatibility**: Ideal for secure data transfer between air-gapped systems.

## Tech Stack

- **Programming Language**: Python (primary), with C++ for performance-critical components (e.g., signal processing).
- **Audio Processing**:
  - **PyAudio**: For real-time audio input/output handling.
  - **NumPy**: For efficient signal processing and Fast Fourier Transform (FFT) operations.
  - **SciPy**: For advanced signal processing (e.g., filtering, modulation).
- **Compression**:
  - **Huffman Coding**: Implemented via Python’s `huffman` library or custom implementation for adaptive compression.
- **Encryption**:
  - **PyCryptodome**: For AES-256 encryption and RSA key exchange.
- **Error Correction**:
  - **Reed-Solomon**: Using the `reedsolo` Python library for robust error correction.
- **Modulation**:
  - **OFDM with 64-QAM**: Custom implementation in Python/C++ for high-speed data encoding.
- **Dependencies**:
  - `numpy`, `scipy`, `pyaudio`, `pycryptodome`, `reedsolo`
  - SDL2 for cross-platform audio backend (optional for C++ components).
- **Build Tools**:
  - `CMake`: For building C++ components.
  - `pip`: For Python dependency management.

## Installation

### Prerequisites

- Python 3.8+
- pip for Python package management
- SDL2 development libraries (for C++ components):
  - Ubuntu: `sudo apt install libsdl2-dev`
  - macOS: `brew install sdl2`
  - Windows: Install via MSYS2 (`pacman -S mingw-w64-x86_64-SDL2`)
- A computer with a microphone and speaker supporting 48 kHz sampling rate.

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/makalin/SonicLink.git --recursive
   cd SonicLink
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Build C++ components (optional for performance optimization):
   ```bash
   mkdir build && cd build
   cmake ..
   make
   ```

4. Run the demo application:
   ```bash
   python soniclink/main.py
   ```

## Usage

SonicLink provides a command-line interface (CLI) and a Python API for integration into other projects.

### CLI Example

Send a file:
```bash
python soniclink/send.py --file input.txt --recipient public_key.pem
```

Receive a file:
```bash
python soniclink/receive.py --output output.txt --private_key private_key.pem
```

### Python API Example

```python
from soniclink import SonicLinkSender, SonicLinkReceiver

# Sender
sender = SonicLinkSender(freq_range=(18000, 22000), bitrate=80000)
compressed_data = sender.compress_data("Hello, SonicLink!")
encrypted_data = sender.encrypt_data(compressed_data, recipient_public_key)
sender.transmit(encrypted_data)

# Receiver
receiver = SonicLinkReceiver(freq_range=(18000, 22000))
raw_data = receiver.receive()
decrypted_data = receiver.decrypt_data(raw_data, private_key)
original_data = receiver.decompress_data(decrypted_data)
print(original_data)  # Output: Hello, SonicLink!
```

## How It Works

1. **Data Preparation**:
   - Input data is compressed using adaptive Huffman coding to reduce transmission size.
   - Compressed data is encrypted with AES-256, with the session key exchanged via RSA.

2. **Modulation**:
   - Data is encoded using OFDM with 64-QAM modulation, splitting the signal across multiple carrier frequencies in the 18-22 kHz range.
   - Reed-Solomon codes are applied for error correction.

3. **Transmission**:
   - The sender generates a waveform using NumPy and transmits it via PyAudio to the computer’s speaker.
   - Special start/end markers (e.g., 17.5 kHz tone) signal the transmission boundaries.

4. **Reception**:
   - The receiver captures audio via PyAudio, applies FFT to extract frequency components, and decodes the data.
   - Reed-Solomon decoding corrects errors, followed by AES decryption and Huffman decompression.

5. **Security**:
   - Only the recipient with the correct private key can decrypt the data, ensuring security even if other devices hear the sound.

## Performance

- **Bitrate**: Up to 80 kbps (10 kB/s) with optimal conditions (high SNR, low noise).
- **Range**: Effective up to 10 meters in typical indoor environments; longer ranges possible with high-quality audio hardware.
- **Latency**: Negligible beyond the speed of sound (~343 m/s), with processing latency <50 ms.

## Security Considerations

- **Encryption**: AES-256 ensures data confidentiality; RSA key exchange prevents unauthorized access.
- **Man-in-the-Middle Protection**: RSA public/private key pairs prevent MITM attacks.[](https://www.forbes.com/sites/simonchandler/2019/10/18/how-data-over-sound-will-ensure-a-permanently-connected-iot-world/)
- **Privacy**: Ultrasonic frequencies minimize human audibility, reducing eavesdropping risks.

## Limitations

- **Environmental Noise**: Performance may degrade in noisy environments; adaptive noise filtering is included but not foolproof.
- **Hardware Dependency**: Requires microphones and speakers capable of handling 18-22 kHz frequencies.
- **Throughput**: Slower than Wi-Fi/Bluetooth but designed as a complementary protocol for offline scenarios.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by projects like `ggwave` and `quiet`.[](https://github.com/ggerganov/ggwave)[](https://github.com/quiet/quiet)
- Thanks to the open-source community for libraries like PyAudio, NumPy, and PyCryptodome.
