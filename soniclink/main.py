#!/usr/bin/env python3
"""
Main entry point for SonicLink.

This script provides a simple demo and can be used to test the system.
"""

import sys
import time
import logging
from pathlib import Path

# Add the parent directory to the path so we can import soniclink
sys.path.insert(0, str(Path(__file__).parent.parent))

from soniclink import SonicLinkSender, SonicLinkReceiver, CryptoManager
from soniclink.utils import Config, setup_logging, FrequencyRange


def setup_demo():
    """Setup demo environment."""
    print("🎵 SonicLink Demo Setup")
    print("=" * 50)
    
    # Setup logging
    config = Config()
    config.log_level = "INFO"
    setup_logging(config)
    
    # Generate test keys
    print("Generating test RSA key pair...")
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    # Save keys temporarily
    private_path = "demo_private_key.pem"
    public_path = "demo_public_key.pem"
    crypto.save_key_pair(private_key, public_key, private_path, public_path)
    
    print(f"✅ Keys saved to {private_path} and {public_path}")
    return config, private_key, public_key


def demo_text_transmission():
    """Demo text transmission."""
    print("\n📝 Text Transmission Demo")
    print("-" * 30)
    
    config, private_key, public_key = setup_demo()
    
    # Test message
    test_message = "Hello from SonicLink! 🎵 This is a test message sent via ultrasonic waves."
    
    print(f"Test message: {test_message}")
    print(f"Message length: {len(test_message)} characters")
    
    # Create sender and receiver
    freq_range = FrequencyRange(18000, 22000)
    sender = SonicLinkSender(freq_range=freq_range, config=config)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    print("\n🚀 Starting transmission...")
    print("Please ensure your speakers are on and volume is up!")
    
    # Send message
    success = sender.send_text(test_message, public_key)
    
    if success:
        print("✅ Transmission sent successfully!")
        print("\n🎧 Starting reception...")
        print("Please ensure your microphone is working!")
        
        # Receive message
        received_text = receiver.receive_text(private_key=private_key)
        
        if received_text:
            print(f"✅ Message received: {received_text}")
            
            if received_text == test_message:
                print("🎉 SUCCESS: Message transmitted and received correctly!")
            else:
                print("⚠️  WARNING: Received message differs from sent message")
        else:
            print("❌ Failed to receive message")
    else:
        print("❌ Transmission failed")
    
    # Cleanup
    cleanup_demo_files()


def demo_file_transmission():
    """Demo file transmission."""
    print("\n📁 File Transmission Demo")
    print("-" * 30)
    
    config, private_key, public_key = setup_demo()
    
    # Create test file
    test_file = "test_file.txt"
    test_content = """SonicLink File Transmission Test

This is a test file that will be transmitted via ultrasonic waves.
The file contains multiple lines and demonstrates the system's ability
to handle larger data transfers.

Features tested:
- File compression
- AES-256 encryption
- OFDM modulation
- Error correction
- Real-time transmission

🎵 Ultrasonic communication is amazing! 🎵
"""
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file}")
    print(f"File size: {len(test_content)} bytes")
    
    # Create sender and receiver
    freq_range = FrequencyRange(18000, 22000)
    sender = SonicLinkSender(freq_range=freq_range, config=config)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    print("\n🚀 Starting file transmission...")
    print("Please ensure your speakers are on and volume is up!")
    
    # Send file
    success = sender.send_file(test_file, public_key)
    
    if success:
        print("✅ File transmission sent successfully!")
        print("\n🎧 Starting file reception...")
        print("Please ensure your microphone is working!")
        
        # Receive file
        received_file = "received_test_file.txt"
        success = receiver.receive_to_file(received_file, private_key=private_key)
        
        if success:
            print(f"✅ File received and saved to: {received_file}")
            
            # Compare files
            with open(test_file, 'r') as f:
                original_content = f.read()
            
            with open(received_file, 'r') as f:
                received_content = f.read()
            
            if original_content == received_content:
                print("🎉 SUCCESS: File transmitted and received correctly!")
            else:
                print("⚠️  WARNING: Received file differs from original")
        else:
            print("❌ Failed to receive file")
    else:
        print("❌ File transmission failed")
    
    # Cleanup
    cleanup_demo_files()
    for file in [test_file, received_file]:
        if Path(file).exists():
            Path(file).unlink()


def demo_continuous_listening():
    """Demo continuous listening mode."""
    print("\n🎧 Continuous Listening Demo")
    print("-" * 30)
    
    config, private_key, public_key = setup_demo()
    
    freq_range = FrequencyRange(18000, 22000)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    def message_callback(data):
        try:
            text = data.decode('utf-8')
            print(f"\n📨 Received message: {text}")
        except UnicodeDecodeError:
            print(f"\n📨 Received binary data: {len(data)} bytes")
    
    print("Starting continuous listening mode...")
    print("Send messages from another terminal using the send command")
    print("Press Ctrl+C to stop")
    
    try:
        receiver.start_listening(message_callback, private_key)
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping continuous listening...")
        receiver.stop_listening()
    
    # Cleanup
    cleanup_demo_files()


def cleanup_demo_files():
    """Clean up demo files."""
    for file in ["demo_private_key.pem", "demo_public_key.pem"]:
        if Path(file).exists():
            Path(file).unlink()


def show_help():
    """Show help information."""
    print("🎵 SonicLink - High-Speed Ultrasonic Data Communication")
    print("=" * 60)
    print()
    print("Available demos:")
    print("  1. Text transmission demo")
    print("  2. File transmission demo")
    print("  3. Continuous listening demo")
    print("  4. Show help")
    print("  5. Exit")
    print()
    print("Usage:")
    print("  python soniclink/main.py [demo_number]")
    print()
    print("Examples:")
    print("  python soniclink/main.py 1    # Run text transmission demo")
    print("  python soniclink/main.py 2    # Run file transmission demo")
    print("  python soniclink/main.py 3    # Run continuous listening demo")
    print()
    print("CLI Usage:")
    print("  python -m soniclink.cli send 'Hello World'")
    print("  python -m soniclink.cli receive")
    print("  python -m soniclink.cli sendfile myfile.txt")
    print("  python -m soniclink.cli receivefile -o received.txt")
    print("  python -m soniclink.cli generate-keys")
    print("  python -m soniclink.cli devices")
    print("  python -m soniclink.cli test")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        try:
            demo_number = int(sys.argv[1])
        except ValueError:
            print("Invalid demo number. Use 1-5.")
            sys.exit(1)
    else:
        show_help()
        try:
            demo_number = int(input("\nEnter demo number (1-5): "))
        except (ValueError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)
    
    if demo_number == 1:
        demo_text_transmission()
    elif demo_number == 2:
        demo_file_transmission()
    elif demo_number == 3:
        demo_continuous_listening()
    elif demo_number == 4:
        show_help()
    elif demo_number == 5:
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid demo number. Use 1-5.")
        sys.exit(1)


if __name__ == "__main__":
    main() 