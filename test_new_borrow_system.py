#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the new borrow system
"""

from libsys import LibrarySystem

def test_new_borrow_system():
    print("=== ทดสอบระบบยืมใหม่ ===\n")
    
    # สร้าง instance ของระบบ
    library = LibrarySystem()
    
    print("1. ทดสอบแสดงหนังสือที่มีให้ยืม")
    available_books = library._get_available_books_for_borrow()
    
    if available_books:
        print(f"\nพบหนังสือที่ให้ยืม {len(available_books)} รายการ:")
        print("-" * 80)
        print(f"{'ลำดับ':<4} | {'ชื่อหนังสือ':<30} | {'ผู้แต่ง':<20} | {'จำนวนที่ว่าง':<10}")
        print("-" * 80)
        
        for idx, (book_id, title, author, available_quantity) in enumerate(available_books, 1):
            print(f"{idx:<4} | {title:<30} | {author:<20} | {available_quantity} เล่ม")
    else:
        print("ไม่มีหนังสือให้ยืมในขณะนี้")
    
    print("\n2. ทดสอบการคำนวณจำนวนที่ยืม")
    if available_books:
        test_book_id = available_books[0][0]
        borrowed_quantity = library._get_borrowed_quantity(test_book_id)
        print(f"หนังสือ ID: {test_book_id}")
        print(f"จำนวนที่ถูกยืม: {borrowed_quantity} เล่ม")
    
    print("\n3. ทดสอบการแสดงสถิติ")
    library.view_statistics()
    
    print("\n=== การทดสอบเสร็จสิ้น ===")
    print("คุณสามารถทดสอบระบบยืมใหม่ได้โดย:")
    print("1. รันระบบ: python library_system.py")
    print("2. เลือกเมนู '3. จัดการการยืม-คืน'")
    print("3. เลือก '1. ยืมหนังสือ'")
    print("4. ระบบจะแสดงรายการหนังสือที่มีให้ยืม")
    print("5. เลือกหนังสือและจำนวนที่ต้องการยืม (มากสุด 3 เล่ม)")

if __name__ == "__main__":
    test_new_borrow_system()
