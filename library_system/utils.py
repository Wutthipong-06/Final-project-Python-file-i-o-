"""
ฟังก์ชันช่วยเหลือทั่วไป
"""
import struct
from config import Config

def encode_string(text: str, length: int) -> bytes:
    """แปลงสตริงเป็น bytes ตามความยาวที่กำหนด"""
    return text.encode('utf-8')[:length].ljust(length, b'\x00')

def decode_string(data: bytes) -> str:
    """แปลง bytes กลับเป็นสตริง"""
    return data.decode('utf-8').rstrip('\x00')

def get_record_size(format_string: str) -> int:
    """คำนวณขนาดของ record"""
    return struct.calcsize(format_string)