#!/usr/bin/env python3
"""
Simple example demonstrating SonicLink usage.

This example shows how to send and receive text messages
using ultrasonic communication.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soniclink import SonicLinkSender, SonicLinkReceiver, CryptoManager
from soniclink.utils import Config, FrequencyRange


def main():
    """Main example function."""
    print("🎵 SonicLink Simple Example")
    print("=" * 40)
    
    # Setup configuration
    config = Config()
    config.log_level = "INFO"
    
    # Create frequency range (18-22 kHz)
    freq_range = FrequencyRange(18000, 22000)
    
    # Generate encryption keys
    print("Generating encryption keys...")
    crypto = CryptoManager()
    private_key, public_key = crypto.generate_key_pair()
    
    # Create sender and receiver
    print("Initializing SonicLink components...")
    sender = SonicLinkSender(freq_range=freq_range, config=config)
    receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
    
    # Test message
    message = "Hello from SonicLink! 🎵"
    print(f"\nSending message: {message}")
    
    # Send the message
    print("\n🚀 Starting transmission...")
    print("Please ensure your speakers are on and volume is up!")
    
    success = sender.send_text(message, public_key)
    
    if success:
        print("✅ Message sent successfully!")
        
        # Wait a moment
        time.sleep(1)
        
        # Receive the message
        print("\n🎧 Starting reception...")
        print("Please ensure your microphone is working!")
        
        received_message = receiver.receive_text(private_key=private_key)
        
        if received_message:
            print(f"✅ Message received: {received_message}")
            
            if received_message == message:
                print("🎉 SUCCESS: Message transmitted and received correctly!")
            else:
                print("⚠️  WARNING: Received message differs from sent message")
        else:
            print("❌ Failed to receive message")
    else:
        print("❌ Failed to send message")
    
    print("\nExample completed!")


if __name__ == "__main__":
    main() 