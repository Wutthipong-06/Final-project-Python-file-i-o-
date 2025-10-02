
# ไฟล์: config.py
"""
การกำหนดค่าคงที่และโครงสร้างข้อมูล
"""

class Config:
    # โครงสร้างไฟล์
    BOOK_FORMAT = '4s100s50s20s4s1s1s'
    MEMBER_FORMAT = '4s50s50s15s10s1s1s'
    BORROW_FORMAT = '4s4s4s10s10s1s1s'
    
    # ชื่อไฟล์
    BOOKS_FILE = 'books.dat'
    MEMBERS_FILE = 'members.dat'
    BORROWS_FILE = 'borrows.dat'
    REPORT_FILE = 'library_report.txt'
    
    # ข้อกำหนด
    MAX_BORROW_BOOKS = 10
    DUE_DAYS = 7
    
    # สถานะ
    STATUS_ACTIVE = b'A'
    STATUS_BORROWED = b'B'
    STATUS_RETURNED = b'R'
    STATUS_SUSPENDED = b'S'
    STATUS_DELETED = b'1'
    STATUS_NOT_DELETED = b'0'