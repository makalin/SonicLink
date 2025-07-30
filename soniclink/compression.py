"""
Data compression module using Huffman coding for SonicLink.
"""

import heapq
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class HuffmanNode:
    """Node in the Huffman tree."""
    
    def __init__(self, char: Optional[int] = None, freq: int = 0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq


class HuffmanCompressor:
    """
    Adaptive Huffman compressor for data compression.
    
    Uses Huffman coding to compress data by assigning shorter codes
    to more frequent bytes.
    """
    
    def __init__(self):
        """Initialize the Huffman compressor."""
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0
        }
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data using Huffman coding.
        
        Args:
            data: Raw data to compress
            
        Returns:
            Compressed data as bytes
        """
        if not data:
            return b''
        
        try:
            # Count frequencies
            freq_counter = Counter(data)
            
            # Build Huffman tree
            root = self._build_tree(freq_counter)
            
            # Generate codes
            codes = {}
            self._generate_codes(root, "", codes)
            
            # Encode data
            encoded_data = ""
            for byte in data:
                encoded_data += codes[byte]
            
            # Convert to bytes
            compressed_data = self._bitstring_to_bytes(encoded_data)
            
            # Add header with frequency table
            header = self._create_header(freq_counter)
            result = header + compressed_data
            
            # Update stats
            self.compression_stats['original_size'] = len(data)
            self.compression_stats['compressed_size'] = len(result)
            self.compression_stats['compression_ratio'] = len(result) / len(data)
            
            logger.info(f"Compressed {len(data)} bytes to {len(result)} bytes "
                       f"(ratio: {self.compression_stats['compression_ratio']:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return data
    
    def decompress(self, data: bytes) -> Optional[bytes]:
        """
        Decompress data using Huffman coding.
        
        Args:
            data: Compressed data
            
        Returns:
            Decompressed data, or None if decompression failed
        """
        if not data:
            return b''
        
        try:
            # Extract header and frequency table
            freq_counter, compressed_data = self._extract_header(data)
            
            # Rebuild Huffman tree
            root = self._build_tree(freq_counter)
            
            # Convert compressed data to bitstring
            bitstring = self._bytes_to_bitstring(compressed_data)
            
            # Decode data
            decoded_data = []
            current_node = root
            
            for bit in bitstring:
                if bit == '0':
                    current_node = current_node.left
                else:
                    current_node = current_node.right
                
                if current_node.char is not None:
                    decoded_data.append(current_node.char)
                    current_node = root
            
            result = bytes(decoded_data)
            
            logger.info(f"Decompressed {len(data)} bytes to {len(result)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return None
    
    def _build_tree(self, freq_counter: Counter) -> HuffmanNode:
        """Build Huffman tree from frequency counter."""
        # Create leaf nodes
        heap = [HuffmanNode(char, freq) for char, freq in freq_counter.items()]
        heapq.heapify(heap)
        
        # Build tree bottom-up
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            internal = HuffmanNode(freq=left.freq + right.freq)
            internal.left = left
            internal.right = right
            
            heapq.heappush(heap, internal)
        
        return heap[0] if heap else HuffmanNode()
    
    def _generate_codes(self, node: HuffmanNode, code: str, codes: Dict[int, str]):
        """Generate Huffman codes recursively."""
        if node.char is not None:
            codes[node.char] = code
            return
        
        if node.left:
            self._generate_codes(node.left, code + "0", codes)
        if node.right:
            self._generate_codes(node.right, code + "1", codes)
    
    def _bitstring_to_bytes(self, bitstring: str) -> bytes:
        """Convert bitstring to bytes."""
        # Pad with zeros to make length multiple of 8
        padding_length = (8 - len(bitstring) % 8) % 8
        bitstring += "0" * padding_length
        
        # Convert to bytes
        result = bytearray()
        for i in range(0, len(bitstring), 8):
            byte_str = bitstring[i:i+8]
            result.append(int(byte_str, 2))
        
        return bytes(result)
    
    def _bytes_to_bitstring(self, data: bytes) -> str:
        """Convert bytes to bitstring."""
        bitstring = ""
        for byte in data:
            bitstring += format(byte, '08b')
        return bitstring
    
    def _create_header(self, freq_counter: Counter) -> bytes:
        """Create header with frequency table."""
        # Simple header format: [num_unique_bytes][byte1][freq1][byte2][freq2]...
        header = bytearray()
        
        # Number of unique bytes (1 byte)
        header.append(len(freq_counter))
        
        # Frequency table
        for char, freq in freq_counter.items():
            header.append(char)
            # Store frequency as 4 bytes (big-endian)
            header.extend(freq.to_bytes(4, 'big'))
        
        return bytes(header)
    
    def _extract_header(self, data: bytes) -> Tuple[Counter, bytes]:
        """Extract frequency table from header."""
        # Read number of unique bytes
        num_unique = data[0]
        
        # Calculate header size
        header_size = 1 + num_unique * 5  # 1 byte for count + 5 bytes per entry
        
        # Extract frequency table
        freq_counter = Counter()
        for i in range(1, header_size, 5):
            char = data[i]
            freq = int.from_bytes(data[i+1:i+5], 'big')
            freq_counter[char] = freq
        
        # Return frequency table and compressed data
        return freq_counter, data[header_size:]
    
    def get_stats(self) -> Dict[str, any]:
        """Get compression statistics."""
        return self.compression_stats.copy() 