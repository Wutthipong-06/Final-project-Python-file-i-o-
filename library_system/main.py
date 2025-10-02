"""
ไฟล์หลักสำหรับรันโปรแกรม
"""
from file_manager import FileManager
from book_manager import BookManager
from member_manager import MemberManager
from borrow_manager import BorrowManager
from ui import LibraryUI

def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    try:
        # สร้างไฟล์เริ่มต้น
        FileManager.initialize_files()
        
        # สร้าง Managers
        book_mgr = BookManager()
        member_mgr = MemberManager()
        borrow_mgr = BorrowManager(book_mgr, member_mgr)
        
        # เริ่มต้น UI
        ui = LibraryUI(book_mgr, member_mgr, borrow_mgr)
        ui.run()
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดร้ายแรง: {e}")
    finally:
        print("ระบบปิดทำงานแล้ว")

if __name__ == "__main__":
    main()