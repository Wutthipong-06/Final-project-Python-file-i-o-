"""
จัดการข้อมูลสมาชิก
"""
import struct
import datetime
from typing import Optional, List
from config import Config
from utils import encode_string, decode_string, get_record_size
from file_manager import FileManager

class MemberManager:
    def __init__(self):
        self.file_manager = FileManager()
        self.record_size = get_record_size(Config.MEMBER_FORMAT)
    
    def add_member(self, name: str, email: str, phone: str) -> str:
        """เพิ่มสมาชิกใหม่"""
        member_id = self.file_manager.get_next_id(
            Config.MEMBERS_FILE,
            Config.MEMBER_FORMAT,
            self.record_size
        )
        
        join_date = datetime.date.today().strftime("%Y-%m-%d")
        
        member_data = struct.pack(
            Config.MEMBER_FORMAT,
            encode_string(member_id, 4),
            encode_string(name, 50),
            encode_string(email, 50),
            encode_string(phone, 15),
            encode_string(join_date, 10),
            Config.STATUS_ACTIVE,
            Config.STATUS_NOT_DELETED
        )
        
        self.file_manager.append_record(Config.MEMBERS_FILE, member_data)
        return member_id
    
    def find_member_by_id(self, member_id: str) -> Optional[tuple]:
        """ค้นหาสมาชิกจาก ID"""
        members = self.get_all_members()
        for member in members:
            if decode_string(member[0]) == member_id and member[6] == Config.STATUS_NOT_DELETED:
                return member
        return None
    
    def get_all_members(self) -> List:
        """ดึงข้อมูลสมาชิกทั้งหมด"""
        return self.file_manager.read_all_records(
            Config.MEMBERS_FILE,
            Config.MEMBER_FORMAT,
            self.record_size
        )
    
    def ban_member(self, member_id: str) -> bool:
        """แบนสมาชิก"""
        return self._update_member_status(member_id, Config.STATUS_SUSPENDED)
    
    def unban_member(self, member_id: str) -> bool:
        """ยกเลิกการแบนสมาชิก"""
        return self._update_member_status(member_id, Config.STATUS_ACTIVE)
    
    def _update_member_status(self, member_id: str, status: bytes) -> bool:
        """อัพเดทสถานะสมาชิก"""
        members = self.get_all_members()
        for index, member in enumerate(members):
            if decode_string(member[0]) == member_id and member[6] == Config.STATUS_NOT_DELETED:
                updated_member = struct.pack(
                    Config.MEMBER_FORMAT,
                    member[0], member[1], member[2], member[3], member[4],
                    status,
                    member[6]
                )
                self.file_manager.update_record(
                    Config.MEMBERS_FILE,
                    index,
                    updated_member,
                    self.record_size
                )
                return True
        return False

