#!/usr/bin/env python3
"""
Quick start script for SonicLink.

This script helps you get started with SonicLink quickly by:
1. Checking system requirements
2. Installing dependencies
3. Running a simple test
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'numpy',
        'scipy', 
        'pyaudio',
        'pycryptodome',
        'reedsolo',
        'click'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True


def install_dependencies():
    """Install missing dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def run_simple_test():
    """Run a simple test to verify SonicLink works."""
    print("\n🧪 Running simple test...")
    
    try:
        # Import SonicLink components
        from soniclink import SonicLinkSender, SonicLinkReceiver, CryptoManager
        from soniclink.utils import Config, FrequencyRange
        
        print("✅ SonicLink imports successfully")
        
        # Test basic functionality
        config = Config()
        freq_range = FrequencyRange(18000, 22000)
        crypto = CryptoManager()
        
        # Generate keys
        private_key, public_key = crypto.generate_key_pair()
        print("✅ Key generation works")
        
        # Create sender and receiver
        sender = SonicLinkSender(freq_range=freq_range, config=config)
        receiver = SonicLinkReceiver(freq_range=freq_range, config=config)
        print("✅ Sender and receiver created successfully")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 SonicLink is ready to use!")
    print("\nNext steps:")
    print("1. Run the demo: python soniclink/main.py")
    print("2. Try the CLI: python -m soniclink.cli --help")
    print("3. Run examples: python examples/simple_example.py")
    print("4. Run tests: python -m pytest tests/")
    print("\nDocumentation:")
    print("- README.md: Overview and installation")
    print("- examples/: Example scripts")
    print("- tests/: Test suite")


def main():
    """Main quick start function."""
    print("🎵 SonicLink Quick Start")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\nWould you like to install missing dependencies? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                if not install_dependencies():
                    sys.exit(1)
            else:
                print("Please install dependencies manually and run this script again")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nInstallation cancelled")
            sys.exit(1)
    
    # Run simple test
    if not run_simple_test():
        print("\nSonicLink test failed. Please check the installation.")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main() 