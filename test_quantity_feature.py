#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the new quantity feature
"""

from libsys import LibrarySystem
import os

def test_quantity_feature():
    print("=== ทดสอบฟีเจอร์จำนวนหนังสือ ===\n")
    
    # สร้าง instance ของระบบ
    library = LibrarySystem()
    
    print("1. ทดสอบเพิ่มหนังสือพร้อมจำนวน")
    print("   - เพิ่มหนังสือ 'Python Programming' จำนวน 5 เล่ม")
    print("   - เพิ่มหนังสือ 'Data Science' จำนวน 3 เล่ม")
    print("   - เพิ่มหนังสือ 'Web Development' จำนวน 2 เล่ม")
    
    # เพิ่มหนังสือทดสอบ
    test_books = [
        ("Python Programming", "John Doe", "978-1234567890", "2023", 5),
        ("Data Science", "Jane Smith", "978-0987654321", "2023", 3),
        ("Web Development", "Bob Johnson", "978-1122334455", "2023", 2)
    ]
    
    for title, author, isbn, year, quantity in test_books:
        # สร้างข้อมูลหนังสือ
        book_id = library._get_next_id(library.books_file, library.book_size)
        
        book_data = library._encode_string(book_id, 4) + \
                   library._encode_string(title, 100) + \
                   library._encode_string(author, 50) + \
                   library._encode_string(isbn, 20) + \
                   library._encode_string(year, 4) + \
                   library._encode_string(str(quantity), 4) + \
                   b'A' + b'0'
        
        # บันทึกลงไฟล์
        with open(library.books_file, 'ab') as f:
            f.write(book_data)
        
        print(f"   ✓ เพิ่มหนังสือ: {title} (จำนวน: {quantity} เล่ม) ID: {book_id}")
    
    print("\n2. ทดสอบดูข้อมูลหนังสือทั้งหมด")
    library._view_all_books()
    
    print("\n3. ทดสอบดูสถิติ")
    library.view_statistics()
    
    print("\n4. ทดสอบสร้างรายงาน")
    library.generate_report()
    
    print("\n=== การทดสอบเสร็จสิ้น ===")
    print("คุณสามารถรันระบบหลักด้วยคำสั่ง: python library_system.py")
    print("และลองเพิ่มหนังสือใหม่พร้อมจำนวนได้เลย!")

if __name__ == "__main__":
    test_quantity_feature()
