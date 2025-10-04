#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the complete improved library system
"""

from libsys import LibrarySystem

def test_complete_system():
    print("=== ทดสอบระบบห้องสมุดที่ปรับปรุงแล้ว ===\n")
    
    # สร้าง instance ของระบบ
    library = LibrarySystem()
    
    print("1. ทดสอบการแสดงหนังสือทั้งหมด (แบบใหม่)")
    print("-" * 60)
    books = library._get_all_books()
    active_books = [book for book in books if book[7] == b'0']
    
    if active_books:
        print(f"พบหนังสือทั้งหมด {len(active_books)} รายการ")
        print("-" * 90)
        print(f"{'ลำดับ':<6} | {'ชื่อหนังสือ':<25} | {'ผู้แต่ง':<15} | {'จำนวน':<8} | {'สถานะ':<10}")
        print("-" * 90)
        
        for idx, book in enumerate(active_books, 1):
            library._display_book(book, compact=True, show_id=False, sequence=idx)
    else:
        print("ไม่มีหนังสือในระบบ")
    
    print("\n2. ทดสอบการแสดงหนังสือที่มีให้ยืม")
    print("-" * 60)
    available_books = library._get_available_books_for_borrow()
    
    if available_books:
        print(f"พบหนังสือที่ให้ยืม {len(available_books)} รายการ:")
        print("-" * 90)
        print(f"{'ลำดับ':<4} | {'ชื่อหนังสือ':<30} | {'ผู้แต่ง':<20} | {'จำนวนรวม':<8} | {'ว่าง':<6}")
        print("-" * 90)
        
        for idx, (book_id, title, author, available_quantity, total_quantity, borrowed_quantity) in enumerate(available_books, 1):
            print(f"{idx:<4} | {title:<30} | {author:<20} | {total_quantity} เล่ม | {available_quantity} เล่ม")
    else:
        print("ไม่มีหนังสือให้ยืมในขณะนี้")
    
    print("\n3. ทดสอบการแสดงรายการยืมที่ยังไม่คืน")
    print("-" * 60)
    borrows = library._get_all_borrows()
    active_borrows = [borrow for borrow in borrows if borrow[5] == b'B' and borrow[6] == b'0']
    
    if active_borrows:
        # Group borrows by book and member
        book_member_groups = {}
        for borrow in active_borrows:
            book_id = library._decode_string(borrow[1])
            member_id = library._decode_string(borrow[2])
            key = (book_id, member_id)
            if key not in book_member_groups:
                book_member_groups[key] = []
            book_member_groups[key].append(borrow)

        print(f"พบหนังสือที่ยืมอยู่ {len(active_borrows)} รายการ")
        print(f"จำนวนหนังสือที่ถูกยืม: {len(active_borrows)} เล่ม")
        print("-" * 110)

        for (book_id, member_id), borrow_list in book_member_groups.items():
            book = library._find_book_by_id(book_id)
            member = library._find_member_by_id(member_id)
            
            book_title = library._decode_string(book[1]) if book else f"Book ID: {book_id}"
            member_name = library._decode_string(member[1]) if member else f"Member ID: {member_id}"
            
            borrow_date_str = library._decode_string(borrow_list[0][3])
            borrow_count = len(borrow_list)
            
            print(f"หนังสือ: {book_title}")
            print(f"ผู้ยืม: {member_name} (ID: {member_id})")
            print(f"จำนวนที่ยืม: {borrow_count} เล่ม")
            print(f"วันที่ยืม: {borrow_date_str}")
            print(f"รหัสรายการยืม: {', '.join([library._decode_string(b[0]) for b in borrow_list])}")
            print("-" * 110)
    else:
        print("ไม่มีหนังสือที่ยืมอยู่")
    
    print("\n4. ทดสอบการแสดงสถิติ")
    print("-" * 60)
    library.view_statistics()
    
    print("\n=== การทดสอบเสร็จสิ้น ===")
    print("คุณสามารถทดสอบระบบได้โดย:")
    print("1. รันระบบ: python library_system.py")
    print("2. เลือกเมนู '1. จัดการหนังสือ' → '2. ดูข้อมูลหนังสือ' → '2. ดูหนังสือทั้งหมด'")
    print("   - จะเห็นลำดับ 1-n แทน ID")
    print("   - จะเห็นจำนวนที่ว่างให้ยืม")
    print("3. เลือกเมนู '3. จัดการการยืม-คืน' → '1. ยืมหนังสือ'")
    print("   - จะเห็นรายการหนังสือที่มีให้ยืม")
    print("   - สามารถยืมได้ 1-3 เล่มต่อครั้ง")
    print("4. เลือกเมนู '3. จัดการการยืม-คืน' → '3. ดูรายการยืม' → '3. ดูรายการยืมที่ยังไม่คืน'")
    print("   - จะเห็นจำนวนที่ถูกยืมที่ถูกต้อง")

if __name__ == "__main__":
    test_complete_system()
