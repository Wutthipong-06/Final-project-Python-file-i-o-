"""
จัดการการยืม-คืนหนังสือ
"""
import struct
import datetime
from typing import Optional, List, Tuple
from config import Config
from utils import encode_string, decode_string, get_record_size
from file_manager import FileManager
from book_manager import BookManager
from member_manager import MemberManager

class BorrowManager:
    def __init__(self, book_manager: BookManager, member_manager: MemberManager):
        self.file_manager = FileManager()
        self.book_manager = book_manager
        self.member_manager = member_manager
        self.record_size = get_record_size(Config.BORROW_FORMAT)
    
    def add_borrow(self, book_id: str, member_id: str) -> Optional[str]:
        """เพิ่มรายการยืม"""
        borrow_id = self.file_manager.get_next_id(
            Config.BORROWS_FILE,
            Config.BORROW_FORMAT,
            self.record_size
        )
        
        borrow_date = datetime.date.today().strftime("%Y-%m-%d")
        
        borrow_data = struct.pack(
            Config.BORROW_FORMAT,
            encode_string(borrow_id, 4),
            encode_string(book_id, 4),
            encode_string(member_id, 4),
            encode_string(borrow_date, 10),
            encode_string("", 10),
            Config.STATUS_BORROWED,
            Config.STATUS_NOT_DELETED
        )
        
        self.file_manager.append_record(Config.BORROWS_FILE, borrow_data)
        self.book_manager.update_book_status(book_id, Config.STATUS_BORROWED)
        
        return borrow_id
    
    def return_book(self, book_id: str) -> bool:
        """คืนหนังสือ"""
        borrows = self.get_all_borrows()
        return_date = datetime.date.today().strftime("%Y-%m-%d")
        
        for index, borrow in enumerate(borrows):
            if (decode_string(borrow[1]) == book_id and 
                borrow[5] == Config.STATUS_BORROWED and 
                borrow[6] == Config.STATUS_NOT_DELETED):
                
                updated_borrow = struct.pack(
                    Config.BORROW_FORMAT,
                    borrow[0], borrow[1], borrow[2], borrow[3],
                    encode_string(return_date, 10),
                    Config.STATUS_RETURNED,
                    borrow[6]
                )
                
                self.file_manager.update_record(
                    Config.BORROWS_FILE,
                    index,
                    updated_borrow,
                    self.record_size
                )
                
                self.book_manager.update_book_status(book_id, Config.STATUS_ACTIVE)
                return True
        return False
    
    def get_all_borrows(self) -> List:
        """ดึงรายการยืมทั้งหมด"""
        return self.file_manager.read_all_records(
            Config.BORROWS_FILE,
            Config.BORROW_FORMAT,
            self.record_size
        )
    
    def check_and_ban_overdue_members(self) -> List[str]:
        """ตรวจสอบและแบนสมาชิกที่เกินกำหนด"""
        borrows = self.get_all_borrows()
        current_date = datetime.date.today()
        banned_members = []
        
        for borrow in borrows:
            if borrow[5] == Config.STATUS_BORROWED and borrow[6] == Config.STATUS_NOT_DELETED:
                try:
                    borrow_date = datetime.datetime.strptime(
                        decode_string(borrow[3]), "%Y-%m-%d"
                    ).date()
                    due_date = borrow_date + datetime.timedelta(days=Config.DUE_DAYS)
                    days_overdue = (current_date - due_date).days
                    
                    if days_overdue > 0:
                        member_id = decode_string(borrow[2])
                        member = self.member_manager.find_member_by_id(member_id)
                        
                        if member and member[5] == Config.STATUS_ACTIVE:
                            self.member_manager.ban_member(member_id)
                            if member_id not in banned_members:
                                banned_members.append(member_id)
                except:
                    pass
        
        return banned_members
    
    def has_overdue_books(self, member_id: str) -> bool:
        """ตรวจสอบว่ามีหนังสือค้างคืนหรือไม่"""
        borrows = self.get_all_borrows()
        current_date = datetime.date.today()
        
        for borrow in borrows:
            if (decode_string(borrow[2]) == member_id and 
                borrow[5] == Config.STATUS_BORROWED and 
                borrow[6] == Config.STATUS_NOT_DELETED):
                try:
                    borrow_date = datetime.datetime.strptime(
                        decode_string(borrow[3]), "%Y-%m-%d"
                    ).date()
                    due_date = borrow_date + datetime.timedelta(days=Config.DUE_DAYS)
                    if (current_date - due_date).days > 0:
                        return True
                except:
                    pass
        return False