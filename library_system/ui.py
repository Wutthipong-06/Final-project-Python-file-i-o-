"""
ส่วนติดต่อผู้ใช้ (User Interface)
"""
import datetime
from typing import Optional
from config import Config
from utils import decode_string
from book_manager import BookManager
from member_manager import MemberManager
from borrow_manager import BorrowManager

class LibraryUI:
    def __init__(self, book_mgr: BookManager, member_mgr: MemberManager, borrow_mgr: BorrowManager):
        self.book_mgr = book_mgr
        self.member_mgr = member_mgr
        self.borrow_mgr = borrow_mgr
        self.operation_history = []
    
    def show_main_menu(self):
        """แสดงเมนูหลัก"""
        print("\n" + "=" * 60)
        print("ระบบจัดการห้องสมุด (Library Management System)")
        print("=" * 60)
        print("1. จัดการหนังสือ")
        print("2. จัดการสมาชิก")
        print("3. จัดการการยืม-คืน")
        print("4. ดูสถิติ")
        print("0. ออกจากระบบ")
        print("-" * 60)
    
    def add_book_ui(self):
        """UI สำหรับเพิ่มหนังสือ"""
        print("\n=== เพิ่มหนังสือ ===")
        try:
            title = input("ชื่อหนังสือ: ").strip()
            if not title:
                print("กรุณากรอกชื่อหนังสือ")
                return
            
            author = input("ผู้แต่ง: ").strip()
            if not author:
                print("กรุณากรอกชื่อผู้แต่ง")
                return
            
            isbn = input("ISBN: ").strip()
            year_str = input("ปีที่พิมพ์: ").strip()
            
            year = int(year_str)
            if year < 1000 or year > 9999:
                print("ปีที่พิมพ์ต้องเป็นตัวเลข 4 หลัก")
                return
            
            book_id = self.book_mgr.add_book(title, author, isbn, year)
            print(f"เพิ่มหนังสือเรียบร้อย ID: {book_id}")
            self.operation_history.append(f"{datetime.datetime.now()}: เพิ่มหนังสือ '{title}' ID: {book_id}")
            
        except ValueError:
            print("ปีที่พิมพ์ต้องเป็นตัวเลข")
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
    
    def borrow_books_ui(self):
        """UI สำหรับยืมหนังสือ"""
        print("\n=== ยืมหนังสือ ===")
        
        # ตรวจสอบและแบนสมาชิก
        banned_list = self.borrow_mgr.check_and_ban_overdue_members()
        if banned_list:
            print(f"⚠️  ระบบได้แบนสมาชิก {len(banned_list)} คนที่เกินกำหนดคืน")
        
        try:
            num_books = int(input("\nต้องการยืมกี่เล่ม? (1-10): ").strip())
            if num_books < 1 or num_books > Config.MAX_BORROW_BOOKS:
                print("กรุณากรอกจำนวน 1-10 เล่ม")
                return
            
            member_id = input("กรอก ID สมาชิก: ").strip()
            member = self.member_mgr.find_member_by_id(member_id)
            
            if not member:
                print("ไม่พบสมาชิก")
                return
            
            if member[5] == Config.STATUS_SUSPENDED:
                print("=" * 60)
                print("🚫 สมาชิกถูกแบน!")
                print(f"สมาชิก: {decode_string(member[1])} (ID: {member_id})")
                print("สาเหตุ: เกินกำหนดคืนหนังสือ")
                print("\n⚠️  กรุณาคืนหนังสือที่ค้างอยู่ก่อน")
                print("=" * 60)
                return
            
            print(f"\n✓ ผู้ยืม: {decode_string(member[1])} (ID: {member_id})")
            print(f"จำนวนหนังสือที่จะยืม: {num_books} เล่ม")
            print("-" * 60)
            
            borrowed_books = []
            borrow_date = datetime.date.today()
            due_date = borrow_date + datetime.timedelta(days=Config.DUE_DAYS)
            
            for i in range(1, num_books + 1):
                print(f"\n📖 หนังสือเล่มที่ {i}/{num_books}")
                book_id = input(f"กรอก ID หนังสือ: ").strip()
                
                book = self.book_mgr.find_book_by_id(book_id)
                if not book:
                    print(f"ไม่พบหนังสือ ID: {book_id}")
                    continue
                
                if book[5] != Config.STATUS_ACTIVE:
                    print(f"หนังสือ '{decode_string(book[1])}' ถูกยืมแล้ว")
                    continue
                
                if book_id in borrowed_books:
                    print("คุณเลือกหนังสือเล่มนี้ไปแล้ว")
                    continue
                
                borrow_id = self.borrow_mgr.add_borrow(book_id, member_id)
                borrowed_books.append(book_id)
                print(f"✓ บันทึกการยืมเรียบร้อย ID: {borrow_id}")
            
            if borrowed_books:
                print("\n" + "=" * 60)
                print("📚 สรุปการยืมหนังสือ")
                print("=" * 60)
                print(f"ผู้ยืม: {decode_string(member[1])}")
                print(f"ID สมาชิก: {member_id}")
                print(f"วันที่ยืม: {borrow_date.strftime('%Y-%m-%d')}")
                print(f"⏰ กำหนดคืน: {due_date.strftime('%Y-%m-%d')}")
                print(f"\nยืมสำเร็จ {len(borrowed_books)} เล่ม")
                print("\n⚠️  หมายเหตุ:")
                print(f"• กรุณาคืนหนังสือภายใน {Config.DUE_DAYS} วัน")
                print("• หากเกินกำหนด ID จะถูกแบนอัตโนมัติ")
                print("=" * 60)
                
                self.operation_history.append(
                    f"{datetime.datetime.now()}: ยืมหนังสือ {len(borrowed_books)} เล่ม โดยสมาชิก ID: {member_id}"
                )
        
        except ValueError:
            print("กรุณากรอกตัวเลขที่ถูกต้อง")
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
    
    def return_book_ui(self):
        """UI สำหรับคืนหนังสือ"""
        print("\n=== คืนหนังสือ ===")
        try:
            book_id = input("กรอก ID หนังสือที่จะคืน: ").strip()
            
            success = self.borrow_mgr.return_book(book_id)
            if success:
                print("✓ คืนหนังสือเรียบร้อย")
                self.operation_history.append(f"{datetime.datetime.now()}: คืนหนังสือ ID: {book_id}")
            else:
                print("ไม่พบรายการยืมหรือคืนแล้ว")
        
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")
    
    def run(self):
        """เริ่มต้นระบบ"""
        print("ยินดีต้อนรับสู่ระบบจัดการห้องสมุด")
        
        while True:
            try:
                self.show_main_menu()
                choice = input("เลือกเมนู (0-4): ").strip()
                
                if choice == '1':
                    self.add_book_ui()
                elif choice == '2':
                    pass  # เพิ่มเมนูสมาชิก
                elif choice == '3':
                    print("\n1. ยืมหนังสือ")
                    print("2. คืนหนังสือ")
                    sub_choice = input("เลือก: ").strip()
                    if sub_choice == '1':
                        self.borrow_books_ui()
                    elif sub_choice == '2':
                        self.return_book_ui()
                elif choice == '0':
                    print("ขอบคุณที่ใช้บริการ!")
                    break
                else:
                    print("กรุณาเลือกเมนูที่ถูกต้อง")
            
            except KeyboardInterrupt:
                print("\n\nระบบถูกปิดโดยผู้ใช้")
                break
            except Exception as e:
                print(f"เกิดข้อผิดพลาด: {e}")