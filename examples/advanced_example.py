#!/usr/bin/env python3
"""
Advanced example demonstrating SonicLink features.

This example shows file transfer and continuous listening capabilities.
"""

import sys
import time
import threading
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soniclink import SonicLinkSender, SonicLinkReceiver, CryptoManager
from soniclink.utils import Config, FrequencyRange, format_file_size


def create_test_file(filename, content):
    """Create a test file with given content."""
    with open(filename, 'w') as f:
        f.write(content)
    return Path(filename)


def file_transfer_example():
    """Demonstrate file transfer capabilities."""
    print("\n📁 File Transfer Example")
    print("-" * 30)
    
    # Setup
    config = Config()
    freq_range = FrequencyRange(18000, 22000)
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    sender = SonicLinkSender(freq_range=freq_range, config=config)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    # Create test file
    test_content = """SonicLink Advanced Example

This is a test file demonstrating SonicLink's file transfer capabilities.
The file contains multiple lines and will be transmitted via ultrasonic waves.

Features demonstrated:
- File compression using Huffman coding
- AES-256 encryption with RSA key exchange
- OFDM modulation with 64-QAM
- Reed-Solomon error correction
- Real-time transmission and reception

🎵 Ultrasonic communication is amazing! 🎵
"""
    
    test_file = create_test_file("test_document.txt", test_content)
    file_size = test_file.stat().st_size
    
    print(f"Created test file: {test_file}")
    print(f"File size: {format_file_size(file_size)}")
    
    # Send file
    print("\n🚀 Sending file...")
    success = sender.send_file(test_file, public_key)
    
    if success:
        print("✅ File sent successfully!")
        
        # Receive file
        print("\n🎧 Receiving file...")
        received_file = "received_document.txt"
        success = receiver.receive_to_file(received_file, private_key=private_key)
        
        if success:
            print(f"✅ File received: {received_file}")
            
            # Compare files
            with open(test_file, 'r') as f:
                original = f.read()
            
            with open(received_file, 'r') as f:
                received = f.read()
            
            if original == received:
                print("🎉 SUCCESS: File transfer completed correctly!")
            else:
                print("⚠️  WARNING: Received file differs from original")
        else:
            print("❌ Failed to receive file")
    else:
        print("❌ Failed to send file")
    
    # Cleanup
    test_file.unlink()
    if Path(received_file).exists():
        Path(received_file).unlink()


def continuous_listening_example():
    """Demonstrate continuous listening capabilities."""
    print("\n🎧 Continuous Listening Example")
    print("-" * 35)
    
    # Setup
    config = Config()
    freq_range = FrequencyRange(18000, 22000)
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    # Message counter
    message_count = 0
    
    def message_handler(data):
        """Handle received messages."""
        nonlocal message_count
        message_count += 1
        
        try:
            text = data.decode('utf-8')
            print(f"\n📨 Message #{message_count}: {text}")
        except UnicodeDecodeError:
            print(f"\n📨 Binary data #{message_count}: {len(data)} bytes")
    
    print("Starting continuous listening mode...")
    print("Send messages from another terminal using:")
    print("  python -m soniclink.cli send 'Your message' --public-key demo_public_key.pem")
    print("Press Ctrl+C to stop")
    
    try:
        # Save public key for external use
        crypto.save_key_pair(private_key, public_key, "demo_private_key.pem", "demo_public_key.pem")
        print("Keys saved as demo_private_key.pem and demo_public_key.pem")
        
        # Start listening
        receiver.start_listening(message_handler, private_key)
        
        # Keep running for 30 seconds
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                print(f"Listening... ({30-i} seconds remaining)")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping continuous listening...")
    finally:
        receiver.stop_listening()
        print(f"Received {message_count} messages total")
        
        # Cleanup
        for key_file in ["demo_private_key.pem", "demo_public_key.pem"]:
            if Path(key_file).exists():
                Path(key_file).unlink()


def performance_test():
    """Test performance with different data sizes."""
    print("\n⚡ Performance Test")
    print("-" * 20)
    
    # Setup
    config = Config()
    freq_range = FrequencyRange(18000, 22000)
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    sender = SonicLinkSender(freq_range=freq_range, config=config)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    # Test different data sizes
    test_sizes = [100, 1000, 10000]  # bytes
    
    for size in test_sizes:
        print(f"\nTesting {format_file_size(size)} data...")
        
        # Generate test data
        test_data = "A" * size
        
        # Measure transmission time
        start_time = time.time()
        success = sender.send_text(test_data, public_key)
        send_time = time.time() - start_time
        
        if success:
            print(f"✅ Sent in {send_time:.2f} seconds")
            
            # Measure reception time
            start_time = time.time()
            received = receiver.receive_text(private_key=private_key)
            receive_time = time.time() - start_time
            
            if received:
                print(f"✅ Received in {receive_time:.2f} seconds")
                total_time = send_time + receive_time
                effective_bitrate = (size * 8) / total_time
                print(f"📊 Effective bitrate: {effective_bitrate/1000:.1f} kbps")
            else:
                print("❌ Failed to receive")
        else:
            print("❌ Failed to send")


def main():
    """Main example function."""
    print("🎵 SonicLink Advanced Example")
    print("=" * 50)
    
    print("This example demonstrates:")
    print("1. File transfer capabilities")
    print("2. Continuous listening mode")
    print("3. Performance testing")
    
    try:
        # Run examples
        file_transfer_example()
        continuous_listening_example()
        performance_test()
        
        print("\n🎉 All examples completed!")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during examples: {e}")


if __name__ == "__main__":
    main() 