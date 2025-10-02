"""
จัดการการอ่านเขียนไฟล์
"""
import os
import struct
from typing import Optional, List, Tuple
from config import Config
from utils import decode_string, encode_string

class FileManager:
    @staticmethod
    def initialize_files():
        """สร้างไฟล์ไบนารีถ้าไม่มี"""
        for filename in [Config.BOOKS_FILE, Config.MEMBERS_FILE, Config.BORROWS_FILE]:
            if not os.path.exists(filename):
                open(filename, 'wb').close()
    
    @staticmethod
    def get_next_id(filename: str, format_string: str, record_size: int) -> str:
        """สร้าง ID ถัดไป"""
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return "0001"
        
        with open(filename, 'rb') as f:
            f.seek(-record_size, 2)
            last_record = f.read(record_size)
        
        last_id = struct.unpack(format_string, last_record)[0]
        last_id_num = int(decode_string(last_id))
        return f"{last_id_num + 1:04d}"
    
    @staticmethod
    def update_record(filename: str, index: int, data: bytes, record_size: int):
        """อัพเดทระเบียนในไฟล์"""
        with open(filename, 'r+b') as f:
            f.seek(index * record_size)
            f.write(data)
    
    @staticmethod
    def read_all_records(filename: str, format_string: str, record_size: int) -> List:
        """อ่านข้อมูลทั้งหมดจากไฟล์"""
        records = []
        if not os.path.exists(filename):
            return records
        
        with open(filename, 'rb') as f:
            while True:
                data = f.read(record_size)
                if not data:
                    break
                record = struct.unpack(format_string, data)
                records.append(record)
        return records
    
    @staticmethod
    def append_record(filename: str, data: bytes):
        """เพิ่มข้อมูลลงในไฟล์"""
        with open(filename, 'ab') as f:
            f.write(data)