#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ระบบจัดการห้องสมุด (Library Management System)
ใช้ไฟล์ไบนารีและโมดูล struct สำหรับจัดเก็บข้อมูล
พร้อมระบบแบน ID อัตโนมัติเมื่อเกินกำหนดคืน 7 วัน
"""

import struct
import os
import datetime
from typing import List

class LibrarySystem:
    def __init__(self):
        # กำหนดโครงสร้างข้อมูลด้วย struct format
        self.book_format = '4s100s50s20s4s1s1s'
        self.book_size = struct.calcsize(self.book_format)
        
        self.member_format = '4s50s50s15s10s1s1s'
        self.member_size = struct.calcsize(self.member_format)
        
        self.borrow_format = '4s4s4s10s10s1s1s'
        self.borrow_size = struct.calcsize(self.borrow_format)
        
        # ชื่อไฟล์
        self.books_file = 'books.dat'
        self.members_file = 'members.dat'
        self.borrows_file = 'borrows.dat'
        self.report_file = 'library_report.txt'
        
        # สร้างไฟล์ถ้าไม่มี
        self._initialize_files()
        
        # ประวัติการทำงาน
        self.operation_history = []

    def _initialize_files(self):
        """สร้างไฟล์ไบนารีถ้าไม่มี"""
        for filename in [self.books_file, self.members_file, self.borrows_file]:
            if not os.path.exists(filename):
                open(filename, 'wb').close()

    def _get_next_id(self, filename: str, record_size: int) -> str:
        """สร้าง ID ถัดไป"""
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return "0001"
        
        with open(filename, 'rb') as f:
            f.seek(-record_size, 2)
            last_record = f.read(record_size)
            
        if filename == self.books_file:
            last_id = struct.unpack(self.book_format, last_record)[0]
        elif filename == self.members_file:
            last_id = struct.unpack(self.member_format, last_record)[0]
        else:
            last_id = struct.unpack(self.borrow_format, last_record)[0]
            
        last_id_num = int(last_id.decode('utf-8').strip('\x00'))
        return f"{last_id_num + 1:04d}"

    def _encode_string(self, text: str, length: int) -> bytes:
        """แปลงสตริงเป็น bytes ตามความยาวที่กำหนด"""
        return text.encode('utf-8')[:length].ljust(length, b'\x00')

    def _decode_string(self, data: bytes) -> str:
        """แปลง bytes กลับเป็นสตริง"""
        return data.decode('utf-8').rstrip('\x00')

    def _check_and_ban_overdue_members(self):
        """ตรวจสอบและแบนสมาชิกที่เกินกำหนดคืน"""
        borrows = self._get_all_borrows()
        current_date = datetime.date.today()
        banned_members = []
        
        for borrow in borrows:
            if borrow[5] == b'B' and borrow[6] == b'0':  # ยืมอยู่และไม่ถูกลบ
                borrow_date_str = self._decode_string(borrow[3])
                try:
                    borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
                    due_date = borrow_date + datetime.timedelta(days=7)
                    days_overdue = (current_date - due_date).days
                    
                    if days_overdue > 0:
                        member_id = self._decode_string(borrow[2])
                        member = self._find_member_by_id(member_id)
                        
                        if member and member[5] == b'A':  # ยังใช้งานอยู่
                            # แบนสมาชิก
                            member_index = self._find_member_index_by_id(member_id)
                            if member_index != -1:
                                banned_member = struct.pack(
                                    self.member_format,
                                    member[0], member[1], member[2], member[3], member[4],
                                    b'S',  # Suspended (ถูกแบน)
                                    member[6]
                                )
                                self._update_record(self.members_file, member_index, banned_member, self.member_size)
                                
                                if member_id not in banned_members:
                                    banned_members.append(member_id)
                except:
                    pass
        
        return banned_members

    # === BOOKS MANAGEMENT ===
    def add_book(self):
        """เพิ่มหนังสือ"""
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
            
            try:
                year = int(year_str)
                if year < 1000 or year > 9999:
                    raise ValueError()
            except ValueError:
                print("ปีที่พิมพ์ต้องเป็นตัวเลข 4 หลัก")
                return

            book_id = self._get_next_id(self.books_file, self.book_size)
            
            book_data = struct.pack(
                self.book_format,
                self._encode_string(book_id, 4),
                self._encode_string(title, 100),
                self._encode_string(author, 50),
                self._encode_string(isbn, 20),
                self._encode_string(str(year), 4),
                b'A',
                b'0'
            )
            
            with open(self.books_file, 'ab') as f:
                f.write(book_data)
            
            print(f"เพิ่มหนังสือเรียบร้อย ID: {book_id}")
            self.operation_history.append(f"{datetime.datetime.now()}: เพิ่มหนังสือ '{title}' ID: {book_id}")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def view_books(self):
        """ดูข้อมูลหนังสือ"""
        print("\n=== ดูข้อมูลหนังสือ ===")
        print("1. ดูหนังสือเล่มเดียว")
        print("2. ดูหนังสือทั้งหมด")
        print("3. ดูหนังสือแบบกรอง")
        
        choice = input("เลือก (1-3): ").strip()
        
        if choice == '1':
            self._view_single_book()
        elif choice == '2':
            self._view_all_books()
        elif choice == '3':
            self._view_filtered_books()

    def _view_single_book(self):
        """ดูหนังสือเล่มเดียว"""
        book_id = input("กรอก ID หนังสือ: ").strip()
        book = self._find_book_by_id(book_id)
        
        if book:
            self._display_book(book)
        else:
            print("ไม่พบหนังสือ")

    def _view_all_books(self):
        """ดูหนังสือทั้งหมด"""
        books = self._get_all_books()
        active_books = [book for book in books if book[6] == b'0']
        
        if not active_books:
            print("ไม่มีหนังสือในระบบ")
            return
        
        print(f"\nมีหนังสือทั้งหมด {len(active_books)} เล่ม")
        print("-" * 80)
        
        for book in active_books:
            self._display_book(book, compact=True)

    def _view_filtered_books(self):
        """ดูหนังสือแบบกรอง"""
        print("กรองตาม:")
        print("1. ชื่อหนังสือ")
        print("2. ผู้แต่ง")
        print("3. ปีที่พิมพ์")
        
        filter_choice = input("เลือก (1-3): ").strip()
        keyword = input("คำค้นหา: ").strip().lower()
        
        books = self._get_all_books()
        active_books = [book for book in books if book[6] == b'0']
        filtered_books = []
        
        for book in active_books:
            if filter_choice == '1' and keyword in self._decode_string(book[1]).lower():
                filtered_books.append(book)
            elif filter_choice == '2' and keyword in self._decode_string(book[2]).lower():
                filtered_books.append(book)
            elif filter_choice == '3' and keyword in self._decode_string(book[4]):
                filtered_books.append(book)
        
        if filtered_books:
            print(f"\nพบหนังสือ {len(filtered_books)} เล่ม")
            print("-" * 80)
            for book in filtered_books:
                self._display_book(book, compact=True)
        else:
            print("ไม่พบหนังสือที่ตรงกับเงื่อนไข")

    def _find_book_by_id(self, book_id: str):
        """ค้นหาหนังสือจาก ID"""
        books = self._get_all_books()
        for book in books:
            if self._decode_string(book[0]) == book_id and book[6] == b'0':
                return book
        return None

    def _get_all_books(self) -> List:
        """ดึงข้อมูลหนังสือทั้งหมด"""
        books = []
        if not os.path.exists(self.books_file):
            return books
            
        with open(self.books_file, 'rb') as f:
            while True:
                data = f.read(self.book_size)
                if not data:
                    break
                book = struct.unpack(self.book_format, data)
                books.append(book)
        return books

    def _display_book(self, book, compact=False):
        """แสดงข้อมูลหนังสือ"""
        book_id = self._decode_string(book[0])
        title = self._decode_string(book[1])
        author = self._decode_string(book[2])
        isbn = self._decode_string(book[3])
        year = self._decode_string(book[4])
        status = 'ว่าง' if book[5] == b'A' else 'ถูกยืม'
        
        if compact:
            print(f"ID: {book_id} | {title[:30]:<30} | {author[:20]:<20} | {status}")
        else:
            print(f"ID: {book_id}")
            print(f"ชื่อ: {title}")
            print(f"ผู้แต่ง: {author}")
            print(f"ISBN: {isbn}")
            print(f"ปีที่พิมพ์: {year}")
            print(f"สถานะ: {status}")
            print("-" * 50)

    def update_book(self):
        """แก้ไขข้อมูลหนังสือ"""
        print("\n=== แก้ไขหนังสือ ===")
        book_id = input("กรอก ID หนังสือที่ต้องการแก้ไข: ").strip()
        
        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            print("ไม่พบหนังสือ")
            return
        
        book = self._get_book_by_index(book_index)
        if not book:
            print("เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return
        
        print("ข้อมูลปัจจุบัน:")
        self._display_book(book)
        
        print("\nกรอกข้อมูลใหม่ (Enter เพื่อข้าม):")
        
        title = input(f"ชื่อหนังสือ [{self._decode_string(book[1])}]: ").strip()
        if not title:
            title = self._decode_string(book[1])
            
        author = input(f"ผู้แต่ง [{self._decode_string(book[2])}]: ").strip()
        if not author:
            author = self._decode_string(book[2])
            
        isbn = input(f"ISBN [{self._decode_string(book[3])}]: ").strip()
        if not isbn:
            isbn = self._decode_string(book[3])
            
        year_input = input(f"ปีที่พิมพ์ [{self._decode_string(book[4])}]: ").strip()
        if year_input:
            try:
                year = int(year_input)
                if year < 1000 or year > 9999:
                    raise ValueError()
            except ValueError:
                print("ปีที่พิมพ์ต้องเป็นตัวเลข 4 หลัก")
                return
        else:
            year = int(self._decode_string(book[4]))
        
        updated_book = struct.pack(
            self.book_format,
            book[0],
            self._encode_string(title, 100),
            self._encode_string(author, 50),
            self._encode_string(isbn, 20),
            self._encode_string(str(year), 4),
            book[5],
            book[6]
        )
        
        self._update_record(self.books_file, book_index, updated_book, self.book_size)
        print("แก้ไขข้อมูลหนังสือเรียบร้อย")
        self.operation_history.append(f"{datetime.datetime.now()}: แก้ไขหนังสือ ID: {book_id}")

    def delete_book(self):
        """ลบหนังสือ"""
        print("\n=== ลบหนังสือ ===")
        book_id = input("กรอก ID หนังสือที่ต้องการลบ: ").strip()
        
        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            print("ไม่พบหนังสือ")
            return
        
        book = self._get_book_by_index(book_index)
        if not book:
            print("เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return
        
        print("ข้อมูลหนังสือที่จะลบ:")
        self._display_book(book)
        
        confirm = input("ยืนยันการลบ? (y/N): ").strip().lower()
        if confirm != 'y':
            print("ยกเลิกการลบ")
            return
        
        deleted_book = struct.pack(
            self.book_format,
            book[0], book[1], book[2], book[3], book[4], book[5],
            b'1'
        )
        
        self._update_record(self.books_file, book_index, deleted_book, self.book_size)
        print("ลบหนังสือเรียบร้อย")
        self.operation_history.append(f"{datetime.datetime.now()}: ลบหนังสือ ID: {book_id}")

    def _find_book_index_by_id(self, book_id: str) -> int:
        """หา index ของหนังสือจาก ID"""
        if not os.path.exists(self.books_file):
            return -1
            
        with open(self.books_file, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.book_size)
                if not data:
                    break
                book = struct.unpack(self.book_format, data)
                if self._decode_string(book[0]) == book_id and book[6] == b'0':
                    return index
                index += 1
        return -1

    def _get_book_by_index(self, index: int):
        """ดึงข้อมูลหนังสือจาก index"""
        if not os.path.exists(self.books_file):
            return None
            
        with open(self.books_file, 'rb') as f:
            f.seek(index * self.book_size)
            data = f.read(self.book_size)
            if not data:
                return None
            return struct.unpack(self.book_format, data)

    def _update_record(self, filename: str, index: int, data: bytes, record_size: int):
        """อัพเดทระเบียนในไฟล์"""
        with open(filename, 'r+b') as f:
            f.seek(index * record_size)
            f.write(data)

    # === MEMBERS MANAGEMENT ===
    def add_member(self):
        """เพิ่มสมาชิก"""
        print("\n=== เพิ่มสมาชิก ===")
        try:
            name = input("ชื่อ-นามสกุล: ").strip()
            if not name:
                print("กรุณากรอกชื่อ-นามสกุล")
                return
                
            email = input("อีเมล: ").strip()
            phone = input("โทรศัพท์: ").strip()
            
            member_id = self._get_next_id(self.members_file, self.member_size)
            join_date = datetime.date.today().strftime("%Y-%m-%d")
            
            member_data = struct.pack(
                self.member_format,
                self._encode_string(member_id, 4),
                self._encode_string(name, 50),
                self._encode_string(email, 50),
                self._encode_string(phone, 15),
                self._encode_string(join_date, 10),
                b'A',
                b'0'
            )
            
            with open(self.members_file, 'ab') as f:
                f.write(member_data)
            
            print(f"เพิ่มสมาชิกเรียบร้อย ID: {member_id}")
            self.operation_history.append(f"{datetime.datetime.now()}: เพิ่มสมาชิก '{name}' ID: {member_id}")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def view_members(self):
        """ดูข้อมูลสมาชิก"""
        print("\n=== ดูข้อมูลสมาชิก ===")
        print("1. ดูสมาชิกคนเดียว")
        print("2. ดูสมาชิกทั้งหมด")
        print("3. ดูสมาชิกแบบกรอง")
        
        choice = input("เลือก (1-3): ").strip()
        
        if choice == '1':
            self._view_single_member()
        elif choice == '2':
            self._view_all_members()
        elif choice == '3':
            self._view_filtered_members()

    def _view_single_member(self):
        """ดูสมาชิกคนเดียว"""
        member_id = input("กรอก ID สมาชิก: ").strip()
        member = self._find_member_by_id(member_id)
        
        if member:
            self._display_member(member)
        else:
            print("ไม่พบสมาชิก")

    def _view_all_members(self):
        """ดูสมาชิกทั้งหมด"""
        members = self._get_all_members()
        active_members = [member for member in members if member[6] == b'0']
        
        if not active_members:
            print("ไม่มีสมาชิกในระบบ")
            return
        
        print(f"\nมีสมาชิกทั้งหมด {len(active_members)} คน")
        print("-" * 80)
        
        for member in active_members:
            self._display_member(member, compact=True)

    def _view_filtered_members(self):
        """ดูสมาชิกแบบกรอง"""
        print("กรองตาม:")
        print("1. ชื่อ")
        print("2. อีเมล")
        
        filter_choice = input("เลือก (1-2): ").strip()
        keyword = input("คำค้นหา: ").strip().lower()
        
        members = self._get_all_members()
        active_members = [member for member in members if member[6] == b'0']
        filtered_members = []
        
        for member in active_members:
            if filter_choice == '1' and keyword in self._decode_string(member[1]).lower():
                filtered_members.append(member)
            elif filter_choice == '2' and keyword in self._decode_string(member[2]).lower():
                filtered_members.append(member)
        
        if filtered_members:
            print(f"\nพบสมาชิก {len(filtered_members)} คน")
            print("-" * 80)
            for member in filtered_members:
                self._display_member(member, compact=True)
        else:
            print("ไม่พบสมาชิกที่ตรงกับเงื่อนไข")

    def _find_member_by_id(self, member_id: str):
        """ค้นหาสมาชิกจาก ID"""
        members = self._get_all_members()
        for member in members:
            if self._decode_string(member[0]) == member_id and member[6] == b'0':
                return member
        return None

    def _get_all_members(self) -> List:
        """ดึงข้อมูลสมาชิกทั้งหมด"""
        members = []
        if not os.path.exists(self.members_file):
            return members
            
        with open(self.members_file, 'rb') as f:
            while True:
                data = f.read(self.member_size)
                if not data:
                    break
                member = struct.unpack(self.member_format, data)
                members.append(member)
        return members

    def _display_member(self, member, compact=False):
        """แสดงข้อมูลสมาชิก"""
        member_id = self._decode_string(member[0])
        name = self._decode_string(member[1])
        email = self._decode_string(member[2])
        phone = self._decode_string(member[3])
        join_date = self._decode_string(member[4])
        
        if member[5] == b'A':
            status = 'ใช้งาน'
        elif member[5] == b'S':
            status = 'ถูกแบน (เกินกำหนดคืน)'
        else:
            status = 'ระงับ'
        
        if compact:
            print(f"ID: {member_id} | {name[:25]:<25} | {email[:30]:<30} | {status}")
        else:
            print(f"ID: {member_id}")
            print(f"ชื่อ: {name}")
            print(f"อีเมล: {email}")
            print(f"โทรศัพท์: {phone}")
            print(f"วันที่สมัคร: {join_date}")
            print(f"สถานะ: {status}")
            print("-" * 50)

    def update_member(self):
        """แก้ไขข้อมูลสมาชิก"""
        print("\n=== แก้ไขสมาชิก ===")
        member_id = input("กรอก ID สมาชิกที่ต้องการแก้ไข: ").strip()
        
        member_index = self._find_member_index_by_id(member_id)
        if member_index == -1:
            print("ไม่พบสมาชิก")
            return
        
        member = self._get_member_by_index(member_index)
        if not member:
            print("เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return
        
        print("ข้อมูลปัจจุบัน:")
        self._display_member(member)
        
        print("\nกรอกข้อมูลใหม่ (Enter เพื่อข้าม):")
        
        name = input(f"ชื่อ-นามสกุล [{self._decode_string(member[1])}]: ").strip()
        if not name:
            name = self._decode_string(member[1])
            
        email = input(f"อีเมล [{self._decode_string(member[2])}]: ").strip()
        if not email:
            email = self._decode_string(member[2])
            
        phone = input(f"โทรศัพท์ [{self._decode_string(member[3])}]: ").strip()
        if not phone:
            phone = self._decode_string(member[3])
        
        updated_member = struct.pack(
            self.member_format,
            member[0],
            self._encode_string(name, 50),
            self._encode_string(email, 50),
            self._encode_string(phone, 15),
            member[4],
            member[5],
            member[6]
        )
        
        self._update_record(self.members_file, member_index, updated_member, self.member_size)
        print("แก้ไขข้อมูลสมาชิกเรียบร้อย")
        self.operation_history.append(f"{datetime.datetime.now()}: แก้ไขสมาชิก ID: {member_id}")

    def delete_member(self):
        """ลบสมาชิก"""
        print("\n=== ลบสมาชิก ===")
        member_id = input("กรอก ID สมาชิกที่ต้องการลบ: ").strip()
        
        member_index = self._find_member_index_by_id(member_id)
        if member_index == -1:
            print("ไม่พบสมาชิก")
            return
        
        member = self._get_member_by_index(member_index)
        if not member:
            print("เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return
        
        print("ข้อมูลสมาชิกที่จะลบ:")
        self._display_member(member)
        
        confirm = input("ยืนยันการลบ? (y/N): ").strip().lower()
        if confirm != 'y':
            print("ยกเลิกการลบ")
            return
        
        deleted_member = struct.pack(
            self.member_format,
            member[0], member[1], member[2], member[3], member[4], member[5],
            b'1'
        )
        
        self._update_record(self.members_file, member_index, deleted_member, self.member_size)
        print("ลบสมาชิกเรียบร้อย")
        self.operation_history.append(f"{datetime.datetime.now()}: ลบสมาชิก ID: {member_id}")

    def _find_member_index_by_id(self, member_id: str) -> int:
        """หา index ของสมาชิกจาก ID"""
        if not os.path.exists(self.members_file):
            return -1
            
        with open(self.members_file, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.member_size)
                if not data:
                    break
                member = struct.unpack(self.member_format, data)
                if self._decode_string(member[0]) == member_id and member[6] == b'0':
                    return index
                index += 1
        return -1

    def _get_member_by_index(self, index: int):
        """ดึงข้อมูลสมาชิกจาก index"""
        if not os.path.exists(self.members_file):
            return None
            
        with open(self.members_file, 'rb') as f:
            f.seek(index * self.member_size)
            data = f.read(self.member_size)
            if not data:
                return None
            return struct.unpack(self.member_format, data)

    # === BORROW MANAGEMENT ===
    def add_borrow(self):
        """เพิ่มรายการยืม - รองรับการยืมหลายเล่ม"""
        print("\n=== ยืมหนังสือ ===")
        
        # ตรวจสอบและแบนสมาชิกที่เกินกำหนดก่อน
        banned_list = self._check_and_ban_overdue_members()
        if banned_list:
            print(f"⚠️  ระบบได้แบนสมาชิก {len(banned_list)} คนที่เกินกำหนดคืนหนังสือ")
        
        try:
            num_books_input = input("\nต้องการยืมกี่เล่ม? (1-10): ").strip()
            
            try:
                num_books = int(num_books_input)
                if num_books < 1 or num_books > 10:
                    print("กรุณากรอกจำนวน 1-10 เล่มเท่านั้น")
                    return
            except ValueError:
                print("กรุณากรอกตัวเลขที่ถูกต้อง")
                return
            
            member_id = input("กรอก ID สมาชิก: ").strip()
            
            member = self._find_member_by_id(member_id)
            if not member:
                print("ไม่พบสมาชิก")
                return
            
            # ตรวจสอบสถานะสมาชิก
            if member[5] == b'S':
                print("=" * 60)
                print("🚫 สมาชิกถูกแบน!")
                print("=" * 60)
                print(f"สมาชิก: {self._decode_string(member[1])} (ID: {member_id})")
                print("สาเหตุ: เกินกำหนดคืนหนังสือ")
                print("\n⚠️  กรุณาคืนหนังสือที่ค้างอยู่ก่อน จึงจะสามารถยืมหนังสือใหม่ได้")
                print("=" * 60)
                return
            
            print(f"\n✓ ผู้ยืม: {self._decode_string(member[1])} (ID: {member_id})")
            print(f"จำนวนหนังสือที่จะยืม: {num_books} เล่ม")
            print("-" * 60)
            # 7 วันโดนแบน
            borrowed_books = []
            borrow_date = datetime.date.today()
            borrow_date_str = borrow_date.strftime("%Y-%m-%d")
            due_date = borrow_date + datetime.timedelta(days=7)
            due_date_str = due_date.strftime("%Y-%m-%d")
            
            for i in range(1, num_books + 1):
                print(f"\n📖 หนังสือเล่มที่ {i}/{num_books}")
                book_id = input(f"กรอก ID หนังสือเล่มที่ {i}: ").strip()
                
                book = self._find_book_by_id(book_id)
                if not book:
                    print(f"ไม่พบหนังสือ ID: {book_id}")
                    continue_choice = input("ต้องการกรอก ID ใหม่หรือข้าม? (r=ใหม่, s=ข้าม, c=ยกเลิก): ").strip().lower()
                    
                    if continue_choice == 'r':
                        i -= 1
                        continue
                    elif continue_choice == 'c':
                        print("ยกเลิกการยืมทั้งหมด")
                        return
                    else:
                        continue
                
                if book[5] != b'A':
                    print(f"หนังสือ '{self._decode_string(book[1])}' ถูกยืมแล้ว")
                    continue_choice = input("ต้องการกรอก ID ใหม่หรือข้าม? (r=ใหม่, s=ข้าม, c=ยกเลิก): ").strip().lower()
                    
                    if continue_choice == 'r':
                        i -= 1
                        continue
                    elif continue_choice == 'c':
                        print("ยกเลิกการยืมทั้งหมด")
                        for prev_book_id in borrowed_books:
                            self._update_book_status(prev_book_id, b'A')
                        return
                    else:
                        continue
                
                if book_id in borrowed_books:
                    print("คุณเลือกหนังสือเล่มนี้ไปแล้ว")
                    i -= 1
                    continue
                
                borrow_id = self._get_next_id(self.borrows_file, self.borrow_size)
                
                borrow_data = struct.pack(
                    self.borrow_format,
                    self._encode_string(borrow_id, 4),
                    self._encode_string(book_id, 4),
                    self._encode_string(member_id, 4),
                    self._encode_string(borrow_date_str, 10),
                    self._encode_string("", 10),
                    b'B',
                    b'0'
                )
                
                with open(self.borrows_file, 'ab') as f:
                    f.write(borrow_data)
                
                self._update_book_status(book_id, b'B')
                borrowed_books.append(book_id)
                
                print(f"✓ บันทึกการยืมเรียบร้อย ID: {borrow_id}")
                print(f"  หนังสือ: {self._decode_string(book[1])}")
            
            if borrowed_books:
                print("\n" + "=" * 60)
                print("📚 สรุปการยืมหนังสือ")
                print("=" * 60)
                print(f"ผู้ยืม: {self._decode_string(member[1])}")
                print(f"ID สมาชิก: {member_id}")
                print(f"วันที่ยืม: {borrow_date_str}")
                print(f"⏰ กำหนดคืน: {due_date_str}")
                print(f"\nรายการหนังสือที่ยืมสำเร็จ ({len(borrowed_books)} เล่ม):")
                
                for idx, book_id in enumerate(borrowed_books, 1):
                    book = self._find_book_by_id(book_id)
                    if book:
                        print(f"  {idx}. {self._decode_string(book[1])} (ID: {book_id})")
                
                print("\n⚠️  หมายเหตุสำคัญ:")
                print("• กรุณาคืนหนังสือภายใน 7 วัน")
                print("• หากเกินกำหนดคืน ID จะถูกแบนอัตโนมัติ")
                print("• ID ที่ถูกแบนจะไม่สามารถยืมหนังสือได้จนกว่าจะคืนหนังสือ")
                print("=" * 60)
                
                self.operation_history.append(
                    f"{datetime.datetime.now()}: ยืมหนังสือ {len(borrowed_books)} เล่ม โดยสมาชิก ID: {member_id}"
                )
            else:
                print("\nไม่มีหนังสือที่ยืมสำเร็จ")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def return_book(self):
        """คืนหนังสือ"""
        print("\n=== คืนหนังสือ ===")
        try:
            book_id = input("กรอก ID หนังสือที่จะคืน: ").strip()
            
            borrow_record = self._find_active_borrow_by_book_id(book_id)
            if not borrow_record:
                print("ไม่พบรายการยืมหรือหนังสือคืนแล้ว")
                return
            
            borrow_index, borrow_data = borrow_record
            return_date = datetime.date.today()
            return_date_str = return_date.strftime("%Y-%m-%d")
            
            # คำนวณวันเกินกำหนด
            borrow_date_str = self._decode_string(borrow_data[3])
            borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
            due_date = borrow_date + datetime.timedelta(days=7)
            days_overdue = (return_date - due_date).days
            
            updated_borrow = struct.pack(
                self.borrow_format,
                borrow_data[0],
                borrow_data[1],
                borrow_data[2],
                borrow_data[3],
                self._encode_string(return_date_str, 10),
                b'R',
                borrow_data[6]
            )
            
            self._update_record(self.borrows_file, borrow_index, updated_borrow, self.borrow_size)
            self._update_book_status(book_id, b'A')
            
            book = self._find_book_by_id(book_id)
            member_id = self._decode_string(borrow_data[2])
            member = self._find_member_by_id(member_id)
            
            print("\n" + "=" * 60)
            print("✓ คืนหนังสือเรียบร้อย")
            print("=" * 60)
            print(f"หนังสือ: {self._decode_string(book[1])}")
            print(f"ผู้ยืม: {self._decode_string(member[1])}")
            print(f"ID สมาชิก: {member_id}")
            print(f"วันที่ยืม: {borrow_date_str}")
            print(f"กำหนดคืน: {due_date.strftime('%Y-%m-%d')}")
            print(f"วันที่คืน: {return_date_str}")
            
            if days_overdue > 0:
                print(f"\n🔴 เกินกำหนด: {days_overdue} วัน")
            elif days_overdue == 0:
                print(f"\n✓ คืนตรงเวลา (วันสุดท้าย)")
            else:
                print(f"\n✓ คืนก่อนกำหนด {abs(days_overdue)} วัน")
            
            # ตรวจสอบว่ายังมีหนังสือค้างคืนไหม
            borrows = self._get_all_borrows()
            has_overdue = False
            for borrow in borrows:
                if (self._decode_string(borrow[2]) == member_id and 
                    borrow[5] == b'B' and borrow[6] == b'0'):
                    borrow_date_temp = datetime.datetime.strptime(
                        self._decode_string(borrow[3]), "%Y-%m-%d"
                    ).date()
                    due_date_temp = borrow_date_temp + datetime.timedelta(days=7)
                    if (return_date - due_date_temp).days > 0:
                        has_overdue = True
                        break
            
            # ถ้าไม่มีหนังสือค้างคืนแล้ว ยกเลิกการแบน
            if not has_overdue and member and member[5] == b'S':
                member_index = self._find_member_index_by_id(member_id)
                if member_index != -1:
                    unban_member = struct.pack(
                        self.member_format,
                        member[0], member[1], member[2], member[3], member[4],
                        b'A',  # Active อีกครั้ง
                        member[6]
                    )
                    self._update_record(self.members_file, member_index, unban_member, self.member_size)
                    print("\n✓ ยกเลิกการแบน ID สมาชิกเรียบร้อย")
                    print("  สามารถยืมหนังสือได้ตามปกติ")
            
            print("=" * 60)
            
            self.operation_history.append(f"{datetime.datetime.now()}: คืนหนังสือ ID: {book_id}")
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def view_borrows(self):
        """ดูรายการยืม"""
        print("\n=== ดูรายการยืม ===")
        print("1. ดูรายการยืมเดียว")
        print("2. ดูรายการยืมทั้งหมด")
        print("3. ดูรายการยืมที่ยังไม่คืน")
        print("4. ดูประวัติการยืมของสมาชิก")
        print("5. ดูรายการเกินกำหนดคืน")
        
        choice = input("เลือก (1-5): ").strip()
        
        if choice == '1':
            self._view_single_borrow()
        elif choice == '2':
            self._view_all_borrows()
        elif choice == '3':
            self._view_active_borrows()
        elif choice == '4':
            self._view_member_borrow_history()
        elif choice == '5':
            self._view_overdue_borrows()

    def _view_single_borrow(self):
        """ดูรายการยืมเดียว"""
        borrow_id = input("กรอก ID รายการยืม: ").strip()
        borrow = self._find_borrow_by_id(borrow_id)
        
        if borrow:
            self._display_borrow(borrow)
        else:
            print("ไม่พบรายการยืม")

    def _view_all_borrows(self):
        """ดูรายการยืมทั้งหมด"""
        borrows = self._get_all_borrows()
        active_borrows = [borrow for borrow in borrows if borrow[6] == b'0']
        
        if not active_borrows:
            print("ไม่มีรายการยืมในระบบ")
            return
        
        print(f"\nมีรายการยืมทั้งหมด {len(active_borrows)} รายการ")
        print("-" * 110)
        
        for borrow in active_borrows:
            self._display_borrow(borrow, compact=True)

    def _view_active_borrows(self):
        """ดูรายการยืมที่ยังไม่คืน"""
        borrows = self._get_all_borrows()
        active_borrows = [borrow for borrow in borrows if borrow[5] == b'B' and borrow[6] == b'0']
        
        if not active_borrows:
            print("ไม่มีหนังสือที่ยืมอยู่")
            return
        
        print(f"\nมีหนังสือที่ยืมอยู่ {len(active_borrows)} เล่ม")
        print("-" * 110)
        
        for borrow in active_borrows:
            self._display_borrow(borrow, compact=True)

    def _view_member_borrow_history(self):
        """ดูประวัติการยืมของสมาชิก"""
        member_id = input("กรอก ID สมาชิก: ").strip()
        
        member = self._find_member_by_id(member_id)
        if not member:
            print("ไม่พบสมาชิก")
            return
        
        borrows = self._get_all_borrows()
        member_borrows = [borrow for borrow in borrows 
                         if self._decode_string(borrow[2]) == member_id and borrow[6] == b'0']
        
        if not member_borrows:
            print("ไม่มีประวัติการยืม")
            return
        
        print(f"\nประวัติการยืมของ: {self._decode_string(member[1])} (ID: {member_id})")
        print(f"จำนวนรายการ: {len(member_borrows)}")
        print("-" * 110)
        
        for borrow in member_borrows:
            self._display_borrow(borrow, compact=True)

    def _view_overdue_borrows(self):
        """ดูรายการเกินกำหนดคืน"""
        print("\n=== รายการเกินกำหนดคืน ===")
        
        borrows = self._get_all_borrows()
        current_date = datetime.date.today()
        overdue_list = []
        
        for borrow in borrows:
            if borrow[5] == b'B' and borrow[6] == b'0':
                borrow_date_str = self._decode_string(borrow[3])
                try:
                    borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
                    due_date = borrow_date + datetime.timedelta(days=7)
                    days_overdue = (current_date - due_date).days
                    
                    if days_overdue > 0:
                        overdue_list.append((borrow, days_overdue))
                except:
                    pass
        
        if not overdue_list:
            print("✓ ไม่มีรายการเกินกำหนดคืน")
            return
        
        # เรียงตามจำนวนวันที่เกิน
        overdue_list.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🔴 พบรายการเกินกำหนด {len(overdue_list)} รายการ")
        print("=" * 110)
        
        for idx, (borrow, days_overdue) in enumerate(overdue_list, 1):
            book_id = self._decode_string(borrow[1])
            member_id = self._decode_string(borrow[2])
            book = self._find_book_by_id(book_id)
            member = self._find_member_by_id(member_id)
            
            print(f"\n{idx}. หนังสือ: {self._decode_string(book[1]) if book else 'N/A'}")
            print(f"   ผู้ยืม: {self._decode_string(member[1]) if member else 'N/A'} (ID: {member_id})")
            print(f"   วันที่ยืม: {self._decode_string(borrow[3])}")
            borrow_date = datetime.datetime.strptime(self._decode_string(borrow[3]), "%Y-%m-%d").date()
            due_date = borrow_date + datetime.timedelta(days=7)
            print(f"   กำหนดคืน: {due_date.strftime('%Y-%m-%d')}")
            print(f"   🔴 เกินกำหนด: {days_overdue} วัน")
            print("-" * 110)

    def _find_borrow_by_id(self, borrow_id: str):
        """ค้นหารายการยืมจาก ID"""
        borrows = self._get_all_borrows()
        for borrow in borrows:
            if self._decode_string(borrow[0]) == borrow_id and borrow[6] == b'0':
                return borrow
        return None

    def _find_active_borrow_by_book_id(self, book_id: str):
        """หารายการยืมที่ยังไม่คืนจาก book_id"""
        if not os.path.exists(self.borrows_file):
            return None
            
        with open(self.borrows_file, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.borrow_size)
                if not data:
                    break
                borrow = struct.unpack(self.borrow_format, data)
                if (self._decode_string(borrow[1]) == book_id and 
                    borrow[5] == b'B' and borrow[6] == b'0'):
                    return (index, borrow)
                index += 1
        return None

    def _get_all_borrows(self) -> List:
        """ดึงรายการยืมทั้งหมด"""
        borrows = []
        if not os.path.exists(self.borrows_file):
            return borrows
            
        with open(self.borrows_file, 'rb') as f:
            while True:
                data = f.read(self.borrow_size)
                if not data:
                    break
                borrow = struct.unpack(self.borrow_format, data)
                borrows.append(borrow)
        return borrows

    def _display_borrow(self, borrow, compact=False):
        """แสดงรายการยืม"""
        borrow_id = self._decode_string(borrow[0])
        book_id = self._decode_string(borrow[1])
        member_id = self._decode_string(borrow[2])
        borrow_date_str = self._decode_string(borrow[3])
        return_date = self._decode_string(borrow[4]) or "ยังไม่คืน"
        status = "ยืมอยู่" if borrow[5] == b'B' else "คืนแล้ว"
        
        # คำนวณสถานะกำหนดคืน
        try:
            borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
            due_date = borrow_date + datetime.timedelta(days=7)
            due_date_str = due_date.strftime("%Y-%m-%d")
            
            if borrow[5] == b'B':
                current_date = datetime.date.today()
                days_until_due = (due_date - current_date).days
                if days_until_due < 0:
                    overdue_info = f" (เกิน {abs(days_until_due)} วัน)"
                elif days_until_due == 0:
                    overdue_info = " (ครบกำหนดวันนี้)"
                else:
                    overdue_info = f" (เหลือ {days_until_due} วัน)"
            else:
                overdue_info = ""
        except:
            due_date_str = "-"
            overdue_info = ""
        
        book = self._find_book_by_id(book_id)
        member = self._find_member_by_id(member_id)
        
        book_title = self._decode_string(book[1]) if book else f"Book ID: {book_id}"
        member_name = self._decode_string(member[1]) if member else f"Member ID: {member_id}"
        
        if compact:
            print(f"ID: {borrow_id} | {book_title[:25]:<25} | {member_name[:15]:<15} | ID:{member_id} | {borrow_date_str} | {status}{overdue_info}")
        else:
            print(f"รหัสการยืม: {borrow_id}")
            print(f"หนังสือ: {book_title}")
            print(f"ผู้ยืม: {member_name}")
            print(f"ID สมาชิก: {member_id}")
            print(f"วันที่ยืม: {borrow_date_str}")
            print(f"กำหนดคืน: {due_date_str}")
            print(f"วันที่คืน: {return_date}")
            print(f"สถานะ: {status}{overdue_info}")
            print("-" * 50)

    def _update_book_status(self, book_id: str, status: bytes):
        """อัพเดทสถานะหนังสือ"""
        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            return
        
        book = self._get_book_by_index(book_index)
        if not book:
            return
        
        updated_book = struct.pack(
            self.book_format,
            book[0], book[1], book[2], book[3], book[4],
            status,
            book[6]
        )
        
        self._update_record(self.books_file, book_index, updated_book, self.book_size)

    def delete_borrow(self):
        """ลบรายการยืม"""
        print("\n=== ลบรายการยืม ===")
        borrow_id = input("กรอก ID รายการยืมที่ต้องการลบ: ").strip()
        
        borrow_index = self._find_borrow_index_by_id(borrow_id)
        if borrow_index == -1:
            print("ไม่พบรายการยืม")
            return
        
        borrow = self._get_borrow_by_index(borrow_index)
        if not borrow:
            print("เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return
        
        print("รายการยืมที่จะลบ:")
        self._display_borrow(borrow)
        
        confirm = input("ยืนยันการลบ? (y/N): ").strip().lower()
        if confirm != 'y':
            print("ยกเลิกการลบ")
            return
        
        if borrow[5] == b'B':
            book_id = self._decode_string(borrow[1])
            self._update_book_status(book_id, b'A')
        
        deleted_borrow = struct.pack(
            self.borrow_format,
            borrow[0], borrow[1], borrow[2], borrow[3], borrow[4], borrow[5],
            b'1'
        )
        
        self._update_record(self.borrows_file, borrow_index, deleted_borrow, self.borrow_size)
        print("ลบรายการยืมเรียบร้อย")
        self.operation_history.append(f"{datetime.datetime.now()}: ลบรายการยืม ID: {borrow_id}")

    def _find_borrow_index_by_id(self, borrow_id: str) -> int:
        """หา index ของรายการยืมจาก ID"""
        if not os.path.exists(self.borrows_file):
            return -1
            
        with open(self.borrows_file, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.borrow_size)
                if not data:
                    break
                borrow = struct.unpack(self.borrow_format, data)
                if self._decode_string(borrow[0]) == borrow_id and borrow[6] == b'0':
                    return index
                index += 1
        return -1

    def _get_borrow_by_index(self, index: int):
        """ดึงรายการยืมจาก index"""
        if not os.path.exists(self.borrows_file):
            return None
            
        with open(self.borrows_file, 'rb') as f:
            f.seek(index * self.borrow_size)
            data = f.read(self.borrow_size)
            if not data:
                return None
            return struct.unpack(self.borrow_format, data)

    # === STATISTICS AND REPORTS ===
    def view_statistics(self):
        """ดูสถิติโดยสรุป"""
        print("\n=== สถิติโดยสรุป ===")
        
        books = self._get_all_books()
        active_books = [book for book in books if book[6] == b'0']
        available_books = [book for book in active_books if book[5] == b'A']
        borrowed_books = [book for book in active_books if book[5] == b'B']
        deleted_books = [book for book in books if book[6] == b'1']
        
        members = self._get_all_members()
        active_members = [member for member in members if member[6] == b'0' and member[5] == b'A']
        banned_members = [member for member in members if member[6] == b'0' and member[5] == b'S']
        deleted_members = [member for member in members if member[6] == b'1']
        
        borrows = self._get_all_borrows()
        active_borrows = [borrow for borrow in borrows if borrow[6] == b'0']
        current_borrows = [borrow for borrow in active_borrows if borrow[5] == b'B']
        returned_borrows = [borrow for borrow in active_borrows if borrow[5] == b'R']
        deleted_borrows = [borrow for borrow in borrows if borrow[6] == b'1']
        
        # นับหนังสือเกินกำหนด
        current_date = datetime.date.today()
        overdue_count = 0
        for borrow in current_borrows:
            try:
                borrow_date = datetime.datetime.strptime(
                    self._decode_string(borrow[3]), "%Y-%m-%d"
                ).date()
                due_date = borrow_date + datetime.timedelta(days=7)
                if (current_date - due_date).days > 0:
                    overdue_count += 1
            except:
                pass
        
        print("สถิติหนังสือ:")
        print(f"  - หนังสือทั้งหมด: {len(active_books)} เล่ม")
        print(f"  - หนังสือว่าง: {len(available_books)} เล่ม")
        print(f"  - หนังสือถูกยืม: {len(borrowed_books)} เล่ม")
        print(f"  - หนังสือที่ถูกลบ: {len(deleted_books)} เล่ม")
        
        print("\nสถิติสมาชิก:")
        print(f"  - สมาชิกทั้งหมด: {len(active_members)} คน")
        print(f"  - สมาชิกถูกแบน: {len(banned_members)} คน")
        print(f"  - สมาชิกที่ถูกลบ: {len(deleted_members)} คน")
        
        print("\nสถิติการยืม:")
        print(f"  - รายการยืมทั้งหมด: {len(active_borrows)} รายการ")
        print(f"  - กำลังยืมอยู่: {len(current_borrows)} รายการ")
        print(f"  - เกินกำหนดคืน: {overdue_count} รายการ")
        print(f"  - คืนแล้ว: {len(returned_borrows)} รายการ")
        print(f"  - รายการที่ถูกลบ: {len(deleted_borrows)} รายการ")

    def generate_report(self):
        """สร้างรายงานข้อความ"""
        print("\n=== สร้างรายงาน ===")
        
        try:
            report_content = []
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report_content.append("=" * 80)
            report_content.append("รายงานระบบจัดการห้องสมุด")
            report_content.append("Library Management System Report")
            report_content.append("=" * 80)
            report_content.append(f"วันที่สร้างรายงาน: {current_time}")
            report_content.append("-" * 80)
            
            books = self._get_all_books()
            active_books = [book for book in books if book[6] == b'0']
            available_books = [book for book in active_books if book[5] == b'A']
            borrowed_books = [book for book in active_books if book[5] == b'B']
            deleted_books = [book for book in books if book[6] == b'1']
            
            members = self._get_all_members()
            active_members = [member for member in members if member[6] == b'0' and member[5] == b'A']
            banned_members = [member for member in members if member[6] == b'0' and member[5] == b'S']
            deleted_members = [member for member in members if member[6] == b'1']
            
            borrows = self._get_all_borrows()
            active_borrows = [borrow for borrow in borrows if borrow[6] == b'0']
            current_borrows = [borrow for borrow in active_borrows if borrow[5] == b'B']
            returned_borrows = [borrow for borrow in active_borrows if borrow[5] == b'R']
            deleted_borrows = [borrow for borrow in borrows if borrow[6] == b'1']
            
            current_date = datetime.date.today()
            overdue_count = 0
            for borrow in current_borrows:
                try:
                    borrow_date = datetime.datetime.strptime(
                        self._decode_string(borrow[3]), "%Y-%m-%d"
                    ).date()
                    due_date = borrow_date + datetime.timedelta(days=7)
                    if (current_date - due_date).days > 0:
                        overdue_count += 1
                except:
                    pass
            
            report_content.append("\nสรุปข้อมูลระบบ")
            report_content.append("-" * 40)
            report_content.append("หนังสือ:")
            report_content.append(f"  - จำนวนหนังสือทั้งหมด: {len(active_books)} เล่ม")
            report_content.append(f"  - หนังสือว่าง: {len(available_books)} เล่ม")
            report_content.append(f"  - หนังสือถูกยืม: {len(borrowed_books)} เล่ม")
            report_content.append(f"  - หนังสือที่ถูกลบ: {len(deleted_books)} เล่ม")
            
            report_content.append("\nสมาชิก:")
            report_content.append(f"  - จำนวนสมาชิกทั้งหมด: {len(active_members)} คน")
            report_content.append(f"  - สมาชิกถูกแบน: {len(banned_members)} คน")
            report_content.append(f"  - สมาชิกที่ถูกลบ: {len(deleted_members)} คน")
            
            report_content.append("\nรายการยืม:")
            report_content.append(f"  - รายการยืมทั้งหมด: {len(active_borrows)} รายการ")
            report_content.append(f"  - กำลังยืมอยู่: {len(current_borrows)} รายการ")
            report_content.append(f"  - เกินกำหนดคืน: {overdue_count} รายการ")
            report_content.append(f"  - คืนแล้ว: {len(returned_borrows)} รายการ")
            report_content.append(f"  - รายการที่ถูกลบ: {len(deleted_borrows)} รายการ")
            
            report_content.append("\nข้อมูลไฟล์")
            report_content.append("-" * 40)
            for filename, description in [
                (self.books_file, "หนังสือ"),
                (self.members_file, "สมาชิก"),
                (self.borrows_file, "รายการยืม")
            ]:
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    report_content.append(f"  - ไฟล์{description} ({filename}): {file_size} bytes")
                else:
                    report_content.append(f"  - ไฟล์{description} ({filename}): ไม่พบไฟล์")
            
            if active_borrows:
                book_borrow_count = {}
                for borrow in active_borrows:
                    book_id = self._decode_string(borrow[1])
                    book_borrow_count[book_id] = book_borrow_count.get(book_id, 0) + 1
                
                if book_borrow_count:
                    sorted_books = sorted(book_borrow_count.items(), key=lambda x: x[1], reverse=True)
                    report_content.append("\nหนังสือยอดนิยม (5 อันดับแรก)")
                    report_content.append("-" * 40)
                    
                    for i, (book_id, count) in enumerate(sorted_books[:5], 1):
                        book = self._find_book_by_id(book_id)
                        if book:
                            title = self._decode_string(book[1])
                            report_content.append(f"  {i}. {title} - ถูกยืม {count} ครั้ง")
            
            if self.operation_history:
                report_content.append("\nประวัติการทำงานล่าสุด (10 รายการ)")
                report_content.append("-" * 40)
                recent_operations = self.operation_history[-10:]
                for operation in recent_operations:
                    report_content.append(f"  - {operation}")
            
            report_content.append("\n" + "=" * 80)
            report_content.append("จบรายงาน")
            report_content.append("=" * 80)
            
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_content))
            
            print(f"สร้างรายงานเรียบร้อย: {self.report_file}")
            
            show_report = input("แสดงรายงานหรือไม่? (y/N): ").strip().lower()
            if show_report == 'y':
                print("\n" + "\n".join(report_content))
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการสร้างรายงาน: {e}")

    # === MAIN MENU ===
    def show_main_menu(self):
        """แสดงเมนูหลัก"""
        print("\n" + "=" * 60)
        print("ระบบจัดการห้องสมุด (Library Management System)")
        print("=" * 60)
        print("1. จัดการหนังสือ (Books)")
        print("2. จัดการสมาชิก (Members)")
        print("3. จัดการการยืม-คืน (Borrow/Return)")
        print("4. ดูสถิติโดยสรุป (Statistics)")
        print("5. สร้างรายงาน (Generate Report)")
        print("0. ออกจากระบบ (Exit)")
        print("-" * 60)

    def show_book_menu(self):
        """เมนูจัดการหนังสือ"""
        print("\nเมนูจัดการหนังสือ")
        print("1. เพิ่มหนังสือ (Add)")
        print("2. ดูข้อมูลหนังสือ (View)")
        print("3. แก้ไขหนังสือ (Update)")
        print("4. ลบหนังสือ (Delete)")
        print("0. กลับเมนูหลัก")

    def show_member_menu(self):
        """เมนูจัดการสมาชิก"""
        print("\nเมนูจัดการสมาชิก")
        print("1. เพิ่มสมาชิก (Add)")
        print("2. ดูข้อมูลสมาชิก (View)")
        print("3. แก้ไขสมาชิก (Update)")
        print("4. ลบสมาชิก (Delete)")
        print("0. กลับเมนูหลัก")

    def show_borrow_menu(self):
        """เมนูจัดการการยืม-คืน"""
        print("\nเมนูจัดการการยืม-คืน")
        print("1. ยืมหนังสือ (Borrow)")
        print("2. คืนหนังสือ (Return)")
        print("3. ดูรายการยืม (View Borrows)")
        print("4. ลบรายการยืม (Delete Borrow)")
        print("0. กลับเมนูหลัก")

    def run(self):
        """เรียกใช้งานระบบ"""
        print("ยินดีต้อนรับสู่ระบบจัดการห้องสมุด")
        
        while True:
            try:
                self.show_main_menu()
                choice = input("เลือกเมนู (0-5): ").strip()
                
                if choice == '1':
                    self._handle_book_menu()
                elif choice == '2':
                    self._handle_member_menu()
                elif choice == '3':
                    self._handle_borrow_menu()
                elif choice == '4':
                    self.view_statistics()
                elif choice == '5':
                    self.generate_report()
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

    def _handle_book_menu(self):
        """จัดการเมนูหนังสือ"""
        while True:
            self.show_book_menu()
            choice = input("เลือก (0-4): ").strip()
            
            if choice == '1':
                self.add_book()
            elif choice == '2':
                self.view_books()
            elif choice == '3':
                self.update_book()
            elif choice == '4':
                self.delete_book()
            elif choice == '0':
                break
            else:
                print("กรุณาเลือกเมนูที่ถูกต้อง")

    def _handle_member_menu(self):
        """จัดการเมนูสมาชิก"""
        while True:
            self.show_member_menu()
            choice = input("เลือก (0-4): ").strip()
            
            if choice == '1':
                self.add_member()
            elif choice == '2':
                self.view_members()
            elif choice == '3':
                self.update_member()
            elif choice == '4':
                self.delete_member()
            elif choice == '0':
                break
            else:
                print("กรุณาเลือกเมนูที่ถูกต้อง")

    def _handle_borrow_menu(self):
        """จัดการเมนูการยืม-คืน"""
        while True:
            self.show_borrow_menu()
            choice = input("เลือก (0-4): ").strip()
            
            if choice == '1':
                self.add_borrow()
            elif choice == '2':
                self.return_book()
            elif choice == '3':
                self.view_borrows()
            elif choice == '4':
                self.delete_borrow()
            elif choice == '0':
                break
            else:
                print("กรุณาเลือกเมนูที่ถูกต้อง")


def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    try:
        library = LibrarySystem()
        library.run()
        
    except Exception as e:
        print(f"เกิดข้อผิดพลาดร้ายแรง: {e}")
    finally:
        print("ระบบปิดทำงานแล้ว")


if __name__ == "__main__":
    main()