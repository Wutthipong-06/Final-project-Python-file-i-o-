"""
จัดการข้อมูลหนังสือ
"""
import struct
import datetime
from typing import Optional, List
from config import Config
from utils import encode_string, decode_string, get_record_size
from file_manager import FileManager

class BookManager:
    def __init__(self):
        self.file_manager = FileManager()
        self.record_size = get_record_size(Config.BOOK_FORMAT)
    
    def add_book(self, title: str, author: str, isbn: str, year: int) -> str:
        """เพิ่มหนังสือใหม่"""
        book_id = self.file_manager.get_next_id(
            Config.BOOKS_FILE, 
            Config.BOOK_FORMAT, 
            self.record_size
        )
        
        book_data = struct.pack(
            Config.BOOK_FORMAT,
            encode_string(book_id, 4),
            encode_string(title, 100),
            encode_string(author, 50),
            encode_string(isbn, 20),
            encode_string(str(year), 4),
            Config.STATUS_ACTIVE,
            Config.STATUS_NOT_DELETED
        )
        
        self.file_manager.append_record(Config.BOOKS_FILE, book_data)
        return book_id
    
    def find_book_by_id(self, book_id: str) -> Optional[tuple]:
        """ค้นหาหนังสือจาก ID"""
        books = self.get_all_books()
        for book in books:
            if decode_string(book[0]) == book_id and book[6] == Config.STATUS_NOT_DELETED:
                return book
        return None
    
    def get_all_books(self) -> List:
        """ดึงข้อมูลหนังสือทั้งหมด"""
        return self.file_manager.read_all_records(
            Config.BOOKS_FILE,
            Config.BOOK_FORMAT,
            self.record_size
        )
    
    def update_book_status(self, book_id: str, status: bytes):
        """อัพเดทสถานะหนังสือ"""
        books = self.get_all_books()
        for index, book in enumerate(books):
            if decode_string(book[0]) == book_id and book[6] == Config.STATUS_NOT_DELETED:
                updated_book = struct.pack(
                    Config.BOOK_FORMAT,
                    book[0], book[1], book[2], book[3], book[4],
                    status,
                    book[6]
                )
                self.file_manager.update_record(
                    Config.BOOKS_FILE, 
                    index, 
                    updated_book, 
                    self.record_size
                )
                break
    
    def delete_book(self, book_id: str) -> bool:
        """ลบหนังสือ (soft delete)"""
        books = self.get_all_books()
        for index, book in enumerate(books):
            if decode_string(book[0]) == book_id and book[6] == Config.STATUS_NOT_DELETED:
                deleted_book = struct.pack(
                    Config.BOOK_FORMAT,
                    book[0], book[1], book[2], book[3], book[4], book[5],
                    Config.STATUS_DELETED
                )
                self.file_manager.update_record(
                    Config.BOOKS_FILE,
                    index,
                    deleted_book,
                    self.record_size
                )
                return True
        return False
