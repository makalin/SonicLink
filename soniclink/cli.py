"""
Command-line interface for SonicLink.
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

from .core import SonicLinkSender, SonicLinkReceiver
from .encryption import CryptoManager
from .utils import Config, setup_logging, format_file_size, format_duration


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', type=click.Path(), help='Log file path')
def cli(config, verbose, log_file):
    """SonicLink: High-Speed Ultrasonic Data Communication System"""
    
    # Load configuration
    if config:
        try:
            config_obj = Config.load(config)
        except Exception as e:
            click.echo(f"Error loading config: {e}", err=True)
            sys.exit(1)
    else:
        config_obj = Config()
    
    # Setup logging
    if verbose:
        config_obj.log_level = "DEBUG"
    if log_file:
        config_obj.log_file = log_file
    
    setup_logging(config_obj)
    
    # Store config in context
    click.get_current_context().obj = config_obj


@cli.command()
@click.argument('data', type=str)
@click.option('--public-key', '-k', type=click.Path(exists=True), help='Recipient public key file')
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.option('--bitrate', default=80000, help='Bitrate (bps)')
@click.option('--no-encrypt', is_flag=True, help='Disable encryption')
@click.option('--no-compress', is_flag=True, help='Disable compression')
@click.pass_context
def send(ctx, data, public_key, freq_min, freq_max, bitrate, no_encrypt, no_compress):
    """Send data via ultrasonic communication."""
    
    config = ctx.obj
    
    try:
        # Load public key if provided
        recipient_key = None
        if public_key and not no_encrypt:
            crypto = CryptoManager()
            recipient_key = crypto.load_public_key(public_key)
            click.echo(f"Loaded public key from {public_key}")
        
        # Create sender
        from .utils import FrequencyRange
        freq_range = FrequencyRange(freq_min, freq_max)
        
        sender = SonicLinkSender(
            freq_range=freq_range,
            bitrate=bitrate,
            config=config
        )
        
        # Estimate transmission time
        data_size = len(data.encode('utf-8'))
        estimated_time = data_size * 8 / bitrate
        click.echo(f"Data size: {format_file_size(data_size)}")
        click.echo(f"Estimated transmission time: {format_duration(estimated_time)}")
        click.echo(f"Frequency range: {freq_range}")
        click.echo(f"Bitrate: {bitrate} bps")
        
        # Send data
        click.echo("Starting transmission...")
        success = sender.send_data(
            data=data,
            recipient_public_key=recipient_key,
            compress=not no_compress,
            encrypt=not no_encrypt
        )
        
        if success:
            click.echo("✅ Transmission completed successfully!")
        else:
            click.echo("❌ Transmission failed!", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--private-key', '-k', type=click.Path(exists=True), help='Private key file')
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.option('--timeout', default=30.0, help='Reception timeout (seconds)')
@click.option('--no-decrypt', is_flag=True, help='Disable decryption')
@click.option('--no-decompress', is_flag=True, help='Disable decompression')
@click.pass_context
def receive(ctx, output, private_key, freq_min, freq_max, timeout, no_decrypt, no_decompress):
    """Receive data via ultrasonic communication."""
    
    config = ctx.obj
    
    try:
        # Load private key if provided
        private_key_data = None
        if private_key and not no_decrypt:
            crypto = CryptoManager()
            private_key_data = crypto.load_private_key(private_key)
            click.echo(f"Loaded private key from {private_key}")
        
        # Create receiver
        from .utils import FrequencyRange
        freq_range = FrequencyRange(freq_min, freq_max)
        
        receiver = SonicLinkReceiver(
            freq_range=freq_range,
            config=config
        )
        
        click.echo(f"Listening for data... (timeout: {timeout}s)")
        click.echo(f"Frequency range: {freq_range}")
        
        # Receive data
        if output:
            # Save to file
            success = receiver.receive_to_file(
                output_path=output,
                timeout=timeout,
                private_key=private_key_data
            )
            
            if success:
                click.echo(f"✅ Data received and saved to {output}")
            else:
                click.echo("❌ Reception failed!", err=True)
                sys.exit(1)
        else:
            # Receive as text
            data = receiver.receive_text(
                timeout=timeout,
                private_key=private_key_data
            )
            
            if data:
                click.echo("✅ Data received:")
                click.echo(data)
            else:
                click.echo("❌ Reception failed!", err=True)
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--public-key', '-k', type=click.Path(exists=True), help='Recipient public key file')
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.option('--bitrate', default=80000, help='Bitrate (bps)')
@click.option('--no-encrypt', is_flag=True, help='Disable encryption')
@click.option('--no-compress', is_flag=True, help='Disable compression')
@click.pass_context
def sendfile(ctx, file_path, public_key, freq_min, freq_max, bitrate, no_encrypt, no_compress):
    """Send a file via ultrasonic communication."""
    
    config = ctx.obj
    
    try:
        # Load public key if provided
        recipient_key = None
        if public_key and not no_encrypt:
            crypto = CryptoManager()
            recipient_key = crypto.load_public_key(public_key)
            click.echo(f"Loaded public key from {public_key}")
        
        # Get file info
        file_path = Path(file_path)
        file_size = file_path.stat().st_size
        estimated_time = file_size * 8 / bitrate
        
        click.echo(f"File: {file_path}")
        click.echo(f"Size: {format_file_size(file_size)}")
        click.echo(f"Estimated transmission time: {format_duration(estimated_time)}")
        
        # Create sender
        from .utils import FrequencyRange
        freq_range = FrequencyRange(freq_min, freq_max)
        
        sender = SonicLinkSender(
            freq_range=freq_range,
            bitrate=bitrate,
            config=config
        )
        
        # Send file
        click.echo("Starting file transmission...")
        success = sender.send_file(
            file_path=file_path,
            recipient_public_key=recipient_key
        )
        
        if success:
            click.echo("✅ File transmission completed successfully!")
        else:
            click.echo("❌ File transmission failed!", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--private-key', '-k', type=click.Path(exists=True), help='Private key file')
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.option('--timeout', default=30.0, help='Reception timeout (seconds)')
@click.pass_context
def receivefile(ctx, output, private_key, freq_min, freq_max, timeout):
    """Receive a file via ultrasonic communication."""
    
    config = ctx.obj
    
    try:
        # Load private key if provided
        private_key_data = None
        if private_key:
            crypto = CryptoManager()
            private_key_data = crypto.load_private_key(private_key)
            click.echo(f"Loaded private key from {private_key}")
        
        # Create receiver
        from .utils import FrequencyRange
        freq_range = FrequencyRange(freq_min, freq_max)
        
        receiver = SonicLinkReceiver(
            freq_range=freq_range,
            config=config
        )
        
        click.echo(f"Listening for file... (timeout: {timeout}s)")
        click.echo(f"Frequency range: {freq_range}")
        
        # Receive file
        if not output:
            output = "received_file"
        
        success = receiver.receive_to_file(
            output_path=output,
            timeout=timeout,
            private_key=private_key_data
        )
        
        if success:
            click.echo(f"✅ File received and saved to {output}")
        else:
            click.echo("❌ File reception failed!", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--private-key', '-k', type=click.Path(), help='Private key file path')
@click.option('--public-key', '-p', type=click.Path(), help='Public key file path')
@click.pass_context
def generate_keys(ctx, private_key, public_key):
    """Generate RSA key pair for encryption."""
    
    try:
        crypto = CryptoManager()
        private_key_data, public_key_data = crypto.generate_key_pair()
        
        # Save keys
        private_path = private_key or "private_key.pem"
        public_path = public_key or "public_key.pem"
        
        crypto.save_key_pair(private_key_data, public_key_data, private_path, public_path)
        
        click.echo(f"✅ RSA key pair generated:")
        click.echo(f"   Private key: {private_path}")
        click.echo(f"   Public key: {public_path}")
        
    except Exception as e:
        click.echo(f"Error generating keys: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.pass_context
def devices(ctx, freq_min, freq_max):
    """List available audio devices."""
    
    config = ctx.obj
    
    try:
        from .audio import AudioManager
        
        audio = AudioManager(config)
        devices = audio.get_audio_devices()
        
        click.echo("Available audio devices:")
        click.echo()
        
        click.echo("Input devices:")
        for device in devices['input']:
            click.echo(f"  [{device['index']}] {device['name']}")
            click.echo(f"      Channels: {device['channels']}, Sample rate: {device['sample_rate']} Hz")
        
        click.echo()
        click.echo("Output devices:")
        for device in devices['output']:
            click.echo(f"  [{device['index']}] {device['name']}")
            click.echo(f"      Channels: {device['channels']}, Sample rate: {device['sample_rate']} Hz")
        
        audio.cleanup()
        
    except Exception as e:
        click.echo(f"Error listing devices: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--freq-min', default=18000, help='Minimum frequency (Hz)')
@click.option('--freq-max', default=22000, help='Maximum frequency (Hz)')
@click.pass_context
def test(ctx, freq_min, freq_max):
    """Test audio system and communication."""
    
    config = ctx.obj
    
    try:
        from .audio import AudioManager
        from .utils import FrequencyRange
        
        freq_range = FrequencyRange(freq_min, freq_max)
        
        click.echo("Testing SonicLink audio system...")
        click.echo(f"Frequency range: {freq_range}")
        click.echo()
        
        # Test audio devices
        audio = AudioManager(config)
        devices = audio.get_audio_devices()
        
        if not devices['input']:
            click.echo("❌ No input devices found!", err=True)
            sys.exit(1)
        
        if not devices['output']:
            click.echo("❌ No output devices found!", err=True)
            sys.exit(1)
        
        click.echo("✅ Audio devices detected")
        
        # Test audio levels
        levels = audio.get_audio_levels()
        click.echo(f"Audio levels: Input={levels['input_level']:.3f}, Output={levels['output_level']:.3f}")
        
        # Test transmission
        click.echo("Testing transmission...")
        test_data = "Hello, SonicLink! This is a test message."
        
        sender = SonicLinkSender(freq_range=freq_range, config=config)
        success = sender.send_text(test_data)
        
        if success:
            click.echo("✅ Transmission test passed")
        else:
            click.echo("❌ Transmission test failed", err=True)
        
        audio.cleanup()
        
    except Exception as e:
        click.echo(f"Error during test: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 