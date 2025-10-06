#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library Management System - libsys.system

This module contains the LibrarySystem class: a file-backed simple
library management CLI using fixed-size struct-packed records.
"""

import struct
import os
import datetime
from typing import List


class LibrarySystem:
    def __init__(self):
        # struct formats
        self.book_format = '4s100s50s20s4s4s1s1s'  # Added 4s for quantity field
        self.book_size = struct.calcsize(self.book_format)
        
        # Old format for backward compatibility
        self.old_book_format = '4s100s50s20s4s1s1s'
        self.old_book_size = struct.calcsize(self.old_book_format)

        self.member_format = '4s50s50s15s10s1s1s'
        self.member_size = struct.calcsize(self.member_format)

        self.borrow_format = '4s4s4s10s10s1s1s'
        self.borrow_size = struct.calcsize(self.borrow_format)

        # filenames
        self.books_file = 'books.dat'
        self.members_file = 'members.dat'
        self.borrows_file = 'borrows.dat'
        self.report_file = 'library_report.txt'

        # initialize files
        self._initialize_files()
        
        # migrate old data if needed
        self._migrate_old_data()

        # history
        self.operation_history = []

    def _initialize_files(self):
        for filename in [self.books_file, self.members_file, self.borrows_file]:
            if not os.path.exists(filename):
                open(filename, 'wb').close()

    def _migrate_old_data(self):
        """Migrate old book data to new format with quantity field"""
        if not os.path.exists(self.books_file) or os.path.getsize(self.books_file) == 0:
            return
        
        try:
            # Read all data from the file
            with open(self.books_file, 'rb') as f:
                data = f.read()
            
            # Check if we need to migrate
            if len(data) % self.book_size == 0:
                # Data is already in new format
                return
            
            if len(data) % self.old_book_size != 0:
                # Data is corrupted, skip migration
                print("Warning: Book data file appears to be corrupted. Skipping migration.")
                return
            
            print("Migrating old book data to new format...")
            
            # Create backup
            backup_file = self.books_file + '.backup'
            with open(backup_file, 'wb') as f:
                f.write(data)
            
            # Convert old records to new format
            new_data = b''
            for i in range(0, len(data), self.old_book_size):
                old_record = data[i:i + self.old_book_size]
                if len(old_record) == self.old_book_size:
                    # Unpack old format
                    old_book = struct.unpack(self.old_book_format, old_record)
                    
                    # Pack in new format with quantity = 1
                    new_book = struct.pack(
                        self.book_format,
                        old_book[0],  # id
                        old_book[1],  # title
                        old_book[2],  # author
                        old_book[3],  # isbn
                        old_book[4],  # year
                        self._encode_string("1", 4),  # quantity = 1
                        old_book[5],  # status
                        old_book[6]   # deleted
                    )
                    new_data += new_book
            
            # Write new data
            with open(self.books_file, 'wb') as f:
                f.write(new_data)
            
            print(f"Migration completed. Backup saved as {backup_file}")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            print("Please check your data files manually.")

    def _get_next_id(self, filename: str, record_size: int) -> str:
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
        return text.encode('utf-8')[:length].ljust(length, b'\x00')

    def _decode_string(self, data: bytes) -> str:
        return data.decode('utf-8').rstrip('\x00')

    def _check_and_ban_overdue_members(self):
        borrows = self._get_all_borrows()
        current_date = datetime.date.today()
        banned_members = []

        for borrow in borrows:
            if borrow[5] == b'B' and borrow[6] == b'0':
                borrow_date_str = self._decode_string(borrow[3])
                try:
                    borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
                    due_date = borrow_date + datetime.timedelta(days=7)
                    days_overdue = (current_date - due_date).days

                    if days_overdue > 0:
                        member_id = self._decode_string(borrow[2])
                        member = self._find_member_by_id(member_id)

                        if member and member[5] == b'A':
                            member_index = self._find_member_index_by_id(member_id)
                            if member_index != -1:
                                banned_member = struct.pack(
                                    self.member_format,
                                    member[0], member[1], member[2], member[3], member[4],
                                    b'S',
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
        print("\n" + "=" * 60)
        print(" " * 20 + "📚 เพิ่มหนังสือใหม่ 📚")
        print("=" * 60)
        
        print("\n📝 กรุณากรอกข้อมูลหนังสือ")
        print("─" * 60)
        
        try:
            title = input("\n📖 ชื่อหนังสือ: ").strip()
            if not title:
                print("❌ กรุณากรอกชื่อหนังสือ")
                return

            author = input("✍️  ผู้แต่ง: ").strip()
            if not author:
                print("❌ กรุณากรอกชื่อผู้แต่ง")
                return

            isbn = input("🔢 ISBN: ").strip()
            year_str = input("📅 ปีที่พิมพ์: ").strip()

            try:
                year = int(year_str)
                if year < 1000 or year > 9999:
                    raise ValueError()
            except ValueError:
                print("\n❌ ปีที่พิมพ์ต้องเป็นตัวเลข 4 หลัก (1000-9999)")
                return

            quantity_str = input("📚 จำนวนหนังสือ (เล่ม): ").strip()
            try:
                quantity = int(quantity_str)
                if quantity < 1 or quantity > 9999:
                    raise ValueError()
            except ValueError:
                print("\n❌ จำนวนหนังสือต้องเป็นตัวเลข 1-9999 เล่ม")
                return

            book_id = self._get_next_id(self.books_file, self.book_size)

            # แสดงข้อมูลที่จะบันทึก
            print("\n" + "─" * 60)
            print("📋 ข้อมูลที่จะบันทึก:")
            print("─" * 60)
            print(f"📖 ชื่อหนังสือ: {title}")
            print(f"✍️  ผู้แต่ง: {author}")
            print(f"🔢 ISBN: {isbn}")
            print(f"📅 ปีที่พิมพ์: {year}")
            print(f"📚 จำนวนหนังสือ: {quantity} เล่ม")
            print(f"🆔 ID หนังสือ: {book_id}")
            
            confirm = input("\n❓ ยืนยันการเพิ่มหนังสือ? (y/N): ").strip().lower()
            if confirm != 'y':
                print("\n❌ ยกเลิกการเพิ่มหนังสือ")
                return

            book_data = struct.pack(
                self.book_format,
                self._encode_string(book_id, 4),
                self._encode_string(title, 100),
                self._encode_string(author, 50),
                self._encode_string(isbn, 20),
                self._encode_string(str(year), 4),
                self._encode_string(str(quantity), 4),
                b'A',
                b'0'
            )

            with open(self.books_file, 'ab') as f:
                f.write(book_data)

            print("\n✅ เพิ่มหนังสือเรียบร้อย!")
            print("─" * 60)
            print(f"🆔 ID: {book_id}")
            print(f"📖 ชื่อหนังสือ: {title}")
            print(f"📚 จำนวน: {quantity} เล่ม")
            print(f"📝 บันทึกการดำเนินการ: เพิ่มหนังสือ '{title}' ID: {book_id} จำนวน {quantity} เล่ม")
            self.operation_history.append(f"{datetime.datetime.now()}: เพิ่มหนังสือ '{title}' ID: {book_id} จำนวน {quantity} เล่ม")

        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")

    def view_books(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "📚 ดูข้อมูลหนังสือ 📚")
        print("=" * 60)
        print("\n📋 เลือกประเภทการดูข้อมูล:")
        print("─" * 60)
        print("1. 👤 ดูหนังสือเล่มเดียว")
        print("2. 📊 ดูหนังสือทั้งหมด")
        print("3. 🔍 ดูหนังสือแบบกรอง")

        choice = input("\n❓ เลือก (1-3): ").strip()

        if choice == '1':
            self._view_single_book()
        elif choice == '2':
            self._view_all_books()
        elif choice == '3':
            self._view_filtered_books()
        else:
            print("\n❌ กรุณาเลือกตัวเลือกที่ถูกต้อง (1-3)")

    def _view_single_book(self):
        print("\n" + "─" * 60)
        print("👤 ดูข้อมูลหนังสือเล่มเดียว")
        print("─" * 60)
        
        book_id = input("\n🔍 กรอก ID หนังสือ: ").strip()
        
        if not book_id:
            print("❌ กรุณากรอก ID หนังสือ")
            return
            
        book = self._find_book_by_id(book_id)

        if book:
            print("\n📋 ข้อมูลหนังสือ:")
            self._display_book(book)
        else:
            print(f"\n❌ ไม่พบหนังสือ ID: {book_id}")
            print("💡 กรุณาตรวจสอบ ID และลองใหม่")

    def _view_all_books(self):
        print("\n" + "─" * 60)
        print("📊 ดูข้อมูลหนังสือทั้งหมด")
        print("─" * 60)
        
        books = self._get_all_books()
        active_books = [book for book in books if book[7] == b'0']  # Updated index for deleted flag

        if not active_books:
            print("\n📭 ไม่มีหนังสือในระบบ")
            return

        # Calculate total quantity and available quantity
        total_quantity = 0
        available_quantity = 0
        borrowed_quantity = 0
        
        for book in active_books:
            try:
                quantity = int(self._decode_string(book[5]))
                total_quantity += quantity
                
                # Calculate available quantity for this book
                book_id = self._decode_string(book[0])
                book_borrowed = self._get_borrowed_quantity(book_id)
                book_available = quantity - book_borrowed
                available_quantity += book_available
                borrowed_quantity += book_borrowed
            except:
                total_quantity += 1  # fallback for old records
                available_quantity += 1
                borrowed_quantity += 0

        print(f"\n📈 สรุปข้อมูล:")
        print(f"📚 รายการหนังสือทั้งหมด: {len(active_books)} รายการ")
        print(f"📖 จำนวนหนังสือรวม: {total_quantity} เล่ม")
        print(f"📋 หนังสือว่าง: {available_quantity} เล่ม")
        print(f"📚 หนังสือถูกยืม: {borrowed_quantity} เล่ม")
        print("─" * 100)
        print(f"{'ลำดับ':<4} | {'ID':<6} | {'ชื่อหนังสือ':<30} | {'ผู้แต่ง':<20} | {'จำนวน':<8} | {'สถานะ':<15}")
        print("─" * 100)

        for idx, book in enumerate(active_books, 1):
            book_id = self._decode_string(book[0])
            title = self._decode_string(book[1])
            author = self._decode_string(book[2])
            
            try:
                quantity = int(self._decode_string(book[5]))
            except:
                quantity = 1  # fallback for old records
            
            # Calculate available quantity
            borrowed_quantity_book = self._get_borrowed_quantity(book_id)
            available_quantity_book = quantity - borrowed_quantity_book
            
            # Format status
            if available_quantity_book > 0:
                status = f"{available_quantity_book} ว่าง"
            else:
                status = "ถูกยืมหมด"
            
            # Format the line
            print(f"{idx:<4} | {book_id:<6} | {title[:30]:<30} | {author[:20]:<20} | {quantity:>6} เล่ม | {status:<15}")

        print("─" * 100)
        print(f"📅 ข้อมูลอัปเดตล่าสุด: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("─" * 100)

    def _view_filtered_books(self):
        print("\n" + "─" * 60)
        print("🔍 ดูข้อมูลหนังสือแบบกรอง")
        print("─" * 60)
        
        print("\n📋 เลือกประเภทการกรอง:")
        print("1. 📖 ชื่อหนังสือ")
        print("2. ✍️  ผู้แต่ง")
        print("3. 📅 ปีที่พิมพ์")

        filter_choice = input("\n❓ เลือก (1-3): ").strip()
        
        if filter_choice not in ['1', '2', '3']:
            print("\n❌ กรุณาเลือกตัวเลือกที่ถูกต้อง (1-3)")
            return
            
        keyword = input("🔍 คำค้นหา: ").strip().lower()
        
        if not keyword:
            print("❌ กรุณากรอกคำค้นหา")
            return

        books = self._get_all_books()
        active_books = [book for book in books if book[7] == b'0']  # Updated index for deleted flag
        filtered_books = []

        for book in active_books:
            if filter_choice == '1' and keyword in self._decode_string(book[1]).lower():
                filtered_books.append(book)
            elif filter_choice == '2' and keyword in self._decode_string(book[2]).lower():
                filtered_books.append(book)
            elif filter_choice == '3' and keyword in self._decode_string(book[4]):
                filtered_books.append(book)

        if filtered_books:
            # Calculate total quantity for filtered books
            filtered_quantity = 0
            for book in filtered_books:
                try:
                    quantity_str = self._decode_string(book[5])
                    quantity = int(quantity_str)
                    filtered_quantity += quantity
                except:
                    filtered_quantity += 1  # fallback for old records
            
            print(f"\n✅ พบหนังสือ {len(filtered_books)} รายการ")
            print(f"📚 จำนวนหนังสือรวม: {filtered_quantity} เล่ม")
            print("─" * 90)
            print(f"{'ลำดับ':<6} | {'ชื่อหนังสือ':<25} | {'ผู้แต่ง':<15} | {'จำนวน':<8} | {'สถานะ':<10}")
            print("─" * 90)
            for idx, book in enumerate(filtered_books, 1):
                self._display_book(book, compact=True, show_id=False, sequence=idx)
        else:
            print(f"\n❌ ไม่พบหนังสือที่ตรงกับเงื่อนไข: '{keyword}'")
            print("💡 ลองใช้คำค้นหาอื่น หรือตรวจสอบการสะกด")

    def _find_book_by_id(self, book_id: str):
        books = self._get_all_books()
        for book in books:
            if self._decode_string(book[0]) == book_id and book[7] == b'0':  # Updated index for deleted flag
                return book
        return None

    def _get_all_books(self) -> List:
        books = []
        if not os.path.exists(self.books_file):
            return books

        with open(self.books_file, 'rb') as f:
            while True:
                data = f.read(self.book_size)
                if not data:
                    break
                if len(data) != self.book_size:
                    # Skip incomplete records
                    break
                try:
                    book = struct.unpack(self.book_format, data)
                    books.append(book)
                except struct.error:
                    # Skip corrupted records
                    continue
        return books

    def _display_book(self, book, compact=False, show_id=True, sequence=None):
        book_id = self._decode_string(book[0])
        title = self._decode_string(book[1])
        author = self._decode_string(book[2])
        isbn = self._decode_string(book[3])
        year = self._decode_string(book[4])
        quantity_str = self._decode_string(book[5])
        try:
            quantity = int(quantity_str)
        except:
            quantity = 1  # fallback for old records
        
        # Calculate available quantity
        borrowed_quantity = self._get_borrowed_quantity(book_id)
        available_quantity = quantity - borrowed_quantity

        if compact:
            if show_id:
                print(f"ID: {book_id} | {title[:25]:<25} | {author[:15]:<15} | {quantity} เล่ม | {available_quantity} ว่าง")
            else:
                print(f"{sequence:<6} | {title[:25]:<25} | {author[:15]:<15} | {quantity} เล่ม | {available_quantity} ว่าง")
        else:
            print("┌" + "─" * 50 + "┐")
            print(f"│ {'ข้อมูลหนังสือ':^52} │")
            print("├" + "─" * 50 + "┤")
            print(f"│ ID: {book_id:<44} │")
            print(f"│ ชื่อ: {title[:42]:<44} │")
            print(f"│ ผู้แต่ง: {author[:40]:<42} │")
            print(f"│ ISBN: {isbn[:43]:<42} │")
            print(f"│ ปีที่พิมพ์: {year:<41} │")
            print(f"│ จำนวนรวม: {quantity} เล่ม{'':<33} │")
            print(f"│ จำนวนที่ว่าง: {available_quantity} เล่ม{'':<32} │")
            print(f"│ จำนวนที่ถูกยืม: {borrowed_quantity} เล่ม{'':<31} │")
            print("└" + "─" * 50 + "┘")

    def update_book(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "📚 แก้ไขหนังสือ 📚")
        print("=" * 60)
        
        book_id = input("\n🔍 กรอก ID หนังสือที่ต้องการแก้ไข: ").strip()
        
        if not book_id:
            print("❌ กรุณากรอก ID หนังสือ")
            return

        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            print("\n❌ ไม่พบหนังสือ ID:", book_id)
            print("💡 กรุณาตรวจสอบ ID และลองใหม่")
            return

        book = self._get_book_by_index(book_index)
        if not book:
            print("\n❌ เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return

        print("\n📋 ข้อมูลปัจจุบัน :")
        self._display_book(book)

        print("\n" + "─" * 60)
        print("📝 กรอกข้อมูลใหม่ (กด Enter เพื่อข้ามการแก้ไข)")
        print("─" * 60)

        title = input(f"\n📖 ชื่อหนังสือ [{self._decode_string(book[1])}]: ").strip()
        if not title:
            title = self._decode_string(book[1])

        author = input(f"✍️  ผู้แต่ง [{self._decode_string(book[2])}]: ").strip()
        if not author:
            author = self._decode_string(book[2])

        isbn = input(f"🔢 ISBN [{self._decode_string(book[3])}]: ").strip()
        if not isbn:
            isbn = self._decode_string(book[3])

        year_input = input(f"📅 ปีที่พิมพ์ [{self._decode_string(book[4])}]: ").strip()
        if year_input:
            try:
                year = int(year_input)
                if year < 1000 or year > 9999:
                    raise ValueError()
            except ValueError:
                print("\n❌ ปีที่พิมพ์ต้องเป็นตัวเลข 4 หลัก (1000-9999)")
                return
        else:
            year = int(self._decode_string(book[4]))

        current_quantity = self._decode_string(book[5])
        try:
            current_quantity_int = int(current_quantity)
        except:
            current_quantity_int = 1  # fallback for old records
            current_quantity = "1"

        quantity_input = input(f"📚 จำนวนหนังสือ (เล่ม) [{current_quantity}]: ").strip()
        if quantity_input:
            try:
                quantity = int(quantity_input)
                if quantity < 1 or quantity > 9999:
                    raise ValueError()
            except ValueError:
                print("\n❌ จำนวนหนังสือต้องเป็นตัวเลข 1-9999 เล่ม")
                return
        else:
            quantity = current_quantity_int

        # แสดงข้อมูลที่จะบันทึก
        print("\n" + "─" * 60)
        print("📋 ข้อมูลที่จะบันทึก:")
        print("─" * 60)
        print(f"📖 ชื่อหนังสือ: {title}")
        print(f"✍️  ผู้แต่ง: {author}")
        print(f"🔢 ISBN: {isbn}")
        print(f"📅 ปีที่พิมพ์: {year}")
        print(f"📚 จำนวนหนังสือ: {quantity} เล่ม")
        
        confirm = input("\n❓ ยืนยันการแก้ไขข้อมูล? (y/N): ").strip().lower()
        if confirm != 'y':
            print("\n❌ ยกเลิกการแก้ไข")
            return

        updated_book = struct.pack(
            self.book_format,
            book[0],
            self._encode_string(title, 100),
            self._encode_string(author, 50),
            self._encode_string(isbn, 20),
            self._encode_string(str(year), 4),
            self._encode_string(str(quantity), 4),
            book[6],
            book[7]
        )

        self._update_record(self.books_file, book_index, updated_book, self.book_size)
        print("\n✅ แก้ไขข้อมูลหนังสือเรียบร้อย!")
        print(f"📝 บันทึกการดำเนินการ: แก้ไขหนังสือ ID: {book_id}")
        self.operation_history.append(f"{datetime.datetime.now()}: แก้ไขหนังสือ ID: {book_id}")

    def delete_book(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "🗑️ ลบหนังสือ 🗑️")
        print("=" * 60)
        
        book_id = input("\n🔍 กรอก ID หนังสือที่ต้องการลบ: ").strip()
        
        if not book_id:
            print("❌ กรุณากรอก ID หนังสือ")
            return

        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            print(f"\n❌ ไม่พบหนังสือ ID: {book_id}")
            print("💡 กรุณาตรวจสอบ ID และลองใหม่")
            return

        book = self._get_book_by_index(book_index)
        if not book:
            print("\n❌ เกิดข้อผิดพลาดในการอ่านข้อมูล")
            return

        print("\n⚠️ ข้อมูลหนังสือที่จะลบ:")
        self._display_book(book)

        print("\n" + "─" * 60)
        print("⚠️ คำเตือน: การลบหนังสือจะไม่สามารถกู้คืนได้!")
        print("─" * 60)
        
        confirm = input("\n❓ ยืนยันการลบหนังสือ? (y/N): ").strip().lower()
        if confirm != 'y':
            print("\n❌ ยกเลิกการลบหนังสือ")
            return

        deleted_book = struct.pack(
            self.book_format,
            book[0], book[1], book[2], book[3], book[4], book[5], book[6],
            b'1'
        )

        self._update_record(self.books_file, book_index, deleted_book, self.book_size)
        print("\n✅ ลบหนังสือเรียบร้อย!")
        print("─" * 60)
        print(f"🆔 ID: {book_id}")
        print(f"📖 ชื่อหนังสือ: {self._decode_string(book[1])}")
        print(f"📝 บันทึกการดำเนินการ: ลบหนังสือ ID: {book_id}")
        self.operation_history.append(f"{datetime.datetime.now()}: ลบหนังสือ ID: {book_id}")

    def _find_book_index_by_id(self, book_id: str) -> int:
        if not os.path.exists(self.books_file):
            return -1

        with open(self.books_file, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.book_size)
                if not data:
                    break
                if len(data) != self.book_size:
                    break
                try:
                    book = struct.unpack(self.book_format, data)
                    if self._decode_string(book[0]) == book_id and book[7] == b'0':  # Updated index for deleted flag
                        return index
                except struct.error:
                    pass
                index += 1
        return -1

    def _get_book_by_index(self, index: int):
        if not os.path.exists(self.books_file):
            return None

        with open(self.books_file, 'rb') as f:
            f.seek(index * self.book_size)
            data = f.read(self.book_size)
            if not data or len(data) != self.book_size:
                return None
            try:
                return struct.unpack(self.book_format, data)
            except struct.error:
                return None

    def _update_record(self, filename: str, index: int, data: bytes, record_size: int):
        with open(filename, 'r+b') as f:
            f.seek(index * record_size)
            f.write(data)

    # === MEMBERS MANAGEMENT ===
    def add_member(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "👤 เพิ่มสมาชิกใหม่ 👤")
        print("=" * 60)
        
        print("\n📝 กรุณากรอกข้อมูลสมาชิก")
        print("─" * 60)
        
        try:
            name = input("\n👤 ชื่อ-นามสกุล: ").strip()
            if not name:
                print("❌ กรุณากรอกชื่อ-นามสกุล")
                return

            email = input("📧 อีเมล: ").strip()
            phone = input("📱 โทรศัพท์: ").strip()

            member_id = self._get_next_id(self.members_file, self.member_size)
            join_date = datetime.date.today().strftime("%Y-%m-%d")

            # แสดงข้อมูลที่จะบันทึก
            print("\n" + "─" * 60)
            print("📋 ข้อมูลที่จะบันทึก:")
            print("─" * 60)
            print(f"👤 ชื่อ-นามสกุล: {name}")
            print(f"📧 อีเมล: {email}")
            print(f"📱 โทรศัพท์: {phone}")
            print(f"📅 วันที่สมัคร: {join_date}")
            print(f"🆔 ID สมาชิก: {member_id}")
            
            confirm = input("\n❓ ยืนยันการเพิ่มสมาชิก? (y/N): ").strip().lower()
            if confirm != 'y':
                print("\n❌ ยกเลิกการเพิ่มสมาชิก")
                return

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

            print("\n✅ เพิ่มสมาชิกเรียบร้อย!")
            print("─" * 60)
            print(f"🆔 ID: {member_id}")
            print(f"👤 ชื่อ-นามสกุล: {name}")
            print(f"📅 วันที่สมัคร: {join_date}")
            print(f"📝 บันทึกการดำเนินการ: เพิ่มสมาชิก '{name}' ID: {member_id}")
            self.operation_history.append(f"{datetime.datetime.now()}: เพิ่มสมาชิก '{name}' ID: {member_id}")

        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")

    def view_members(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "👥 ดูข้อมูลสมาชิก 👥")
        print("=" * 60)
        print("\n📋 เลือกประเภทการดูข้อมูล:")
        print("─" * 60)
        print("1. 👤 ดูสมาชิกคนเดียว")
        print("2. 📊 ดูสมาชิกทั้งหมด")
        print("3. 🔍 ดูสมาชิกแบบกรอง")

        choice = input("\n❓ เลือก (1-3): ").strip()

        if choice == '1':
            self._view_single_member()
        elif choice == '2':
            self._view_all_members()
        elif choice == '3':
            self._view_filtered_members()
        else:
            print("\n❌ กรุณาเลือกตัวเลือกที่ถูกต้อง (1-3)")

    def _view_single_member(self):
        print("\n" + "─" * 60)
        print("👤 ดูข้อมูลสมาชิกคนเดียว")
        print("─" * 60)
        
        member_id = input("\n🔍 กรอก ID สมาชิก: ").strip()
        
        if not member_id:
            print("❌ กรุณากรอก ID สมาชิก")
            return
            
        member = self._find_member_by_id(member_id)

        if member:
            print("\n📋 ข้อมูลสมาชิก:")
            self._display_member(member)
        else:
            print(f"\n❌ ไม่พบสมาชิก ID: {member_id}")
            print("💡 กรุณาตรวจสอบ ID และลองใหม่")

    def _view_all_members(self):
        print("\n" + "─" * 60)
        print("📊 ดูข้อมูลสมาชิกทั้งหมด")
        print("─" * 60)
        
        members = self._get_all_members()
        active_members = [member for member in members if member[6] == b'0']

        if not active_members:
            print("\n📭 ไม่มีสมาชิกในระบบ")
            return

        print(f"\n📈 สรุปข้อมูล:")
        print(f"👥 จำนวนสมาชิกทั้งหมด: {len(active_members)} คน")
        print("─" * 80)
        print(f"{'ลำดับ':<4} | {'ID':<6} | {'ชื่อ-นามสกุล':<25} | {'อีเมล':<30} | {'สถานะ':<15}")
        print("─" * 80)
        
        for idx, member in enumerate(active_members, 1):
            self._display_member(member, compact=True, sequence=idx)

    def _view_filtered_members(self):
        print("\n" + "─" * 60)
        print("🔍 ดูข้อมูลสมาชิกแบบกรอง")
        print("─" * 60)
        
        print("\n📋 เลือกประเภทการกรอง:")
        print("1. 👤 ชื่อ-นามสกุล")
        print("2. 📧 อีเมล")

        filter_choice = input("\n❓ เลือก (1-2): ").strip()
        
        if filter_choice not in ['1', '2']:
            print("\n❌ กรุณาเลือกตัวเลือกที่ถูกต้อง (1-2)")
            return
            
        keyword = input("🔍 คำค้นหา: ").strip().lower()
        
        if not keyword:
            print("❌ กรุณากรอกคำค้นหา")
            return

        members = self._get_all_members()
        active_members = [member for member in members if member[6] == b'0']
        filtered_members = []

        for member in active_members:
            if filter_choice == '1' and keyword in self._decode_string(member[1]).lower():
                filtered_members.append(member)
            elif filter_choice == '2' and keyword in self._decode_string(member[2]).lower():
                filtered_members.append(member)

        if filtered_members:
            print(f"\n✅ พบสมาชิก {len(filtered_members)} คน")
            print("─" * 80)
            print(f"{'ลำดับ':<4} | {'ID':<6} | {'ชื่อ-นามสกุล':<25} | {'อีเมล':<30} | {'สถานะ':<15}")
            print("─" * 80)
            for idx, member in enumerate(filtered_members, 1):
                self._display_member(member, compact=True, sequence=idx)
        else:
            print(f"\n❌ ไม่พบสมาชิกที่ตรงกับเงื่อนไข: '{keyword}'")
            print("💡 ลองใช้คำค้นหาอื่น หรือตรวจสอบการสะกด")

    def _find_member_by_id(self, member_id: str):
        members = self._get_all_members()
        for member in members:
            if self._decode_string(member[0]) == member_id and member[6] == b'0':
                return member
        return None

    def _get_all_members(self) -> List:
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

    def _display_member(self, member, compact=False, sequence=None):
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
            if sequence:
                print(f"{sequence:<4} | {member_id:<6} | {name[:25]:<25} | {email[:30]:<30} | {status:<15}")
            else:
                print(f"ID: {member_id} | {name[:25]:<25} | {email[:30]:<30} | {status}")
        else:
            print("┌" + "─" * 50 + "┐")
            print(f"│ {'ข้อมูลสมาชิก':^48} │")
            print("├" + "─" * 50 + "┤")
            print(f"│ ID: {member_id:<44} │")
            print(f"│ ชื่อ-นามสกุล: {name[:38]:<38} │")
            print(f"│ อีเมล: {email[:41]:<41} │")
            print(f"│ โทรศัพท์: {phone[:39]:<39} │")
            print(f"│ วันที่สมัคร: {join_date:<36} │")
            print(f"│ สถานะ: {status:<42} │")
            print("└" + "─" * 50 + "┘")

    def update_member(self):
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
        print("\n" + "=" * 60)
        print(" " * 20 + "📚 ยืมหนังสือ 📚")
        print("=" * 60)
        
        banned_list = self._check_and_ban_overdue_members()
        if banned_list:
            print(f"\n⚠️  ระบบได้แบนสมาชิก {len(banned_list)} คนที่เกินกำหนดคืนหนังสือ")

        try:
            member_id = input("\n🔍 กรอก ID สมาชิก: ").strip()
            
            if not member_id:
                print("❌ กรุณากรอก ID สมาชิก")
                return

            member = self._find_member_by_id(member_id)
            if not member:
                print(f"\n❌ ไม่พบสมาชิก ID: {member_id}")
                print("💡 กรุณาตรวจสอบ ID และลองใหม่")
                return

            if member[5] == b'S':
                print("\n" + "=" * 60)
                print("🚫 สมาชิกถูกแบน!")
                print("=" * 60)
                print(f"👤 สมาชิก: {self._decode_string(member[1])} (ID: {member_id})")
                print("📋 สาเหตุ: เกินกำหนดคืนหนังสือ")
                print("\n⚠️  กรุณาคืนหนังสือที่ค้างอยู่ก่อน จึงจะสามารถยืมหนังสือใหม่ได้")
                print("=" * 60)
                return

            print(f"\n✅ ผู้ยืม: {self._decode_string(member[1])} (ID: {member_id})")
            print("─" * 60)

            # แสดงรายการหนังสือที่มีให้ยืม
            available_books = self._get_available_books_for_borrow()
            if not available_books:
                print("\n📭 ไม่มีหนังสือให้ยืมในขณะนี้")
                return

            print("\n📚 รายการหนังสือที่มีให้ยืม:")
            print("─" * 90)
            print(f"{'ลำดับ':<4} | {'ชื่อหนังสือ':<30} | {'ผู้แต่ง':<20} | {'จำนวนรวม':<8} | {'ว่าง':<6}")
            print("─" * 90)

            for idx, (book_id, title, author, available_quantity, total_quantity, borrowed_quantity) in enumerate(available_books, 1):
                print(f"{idx:<4} | {title:<30} | {author:<20} | {total_quantity} เล่ม | {available_quantity} เล่ม")

            # เลือกหนังสือ
            print("\n" + "─" * 60)
            print("📖 เลือกหนังสือที่ต้องการยืม")
            print("─" * 60)
            choice = input(f"❓ กรอกลำดับหนังสือ (1-{len(available_books)}): ").strip()

            try:
                choice_idx = int(choice) - 1
                if choice_idx < 0 or choice_idx >= len(available_books):
                    print("\n❌ กรุณาเลือกลำดับที่ถูกต้อง")
                    return
            except ValueError:
                print("\n❌ กรุณากรอกตัวเลขที่ถูกต้อง")
                return

            selected_book_id, selected_title, selected_author, available_quantity, total_quantity, borrowed_quantity = available_books[choice_idx]
            
            print(f"\n✅ เลือกหนังสือ: {selected_title}")
            print(f"✍️  ผู้แต่ง: {selected_author}")
            print(f"📚 จำนวนรวม: {total_quantity} เล่ม")
            print(f"📖 ยืมแล้ว: {borrowed_quantity} เล่ม")
            print(f"📋 จำนวนที่ว่างให้ยืม: {available_quantity} เล่ม")

            # เลือกจำนวนที่จะยืม
            max_borrow = min(3, available_quantity)  # ยืมได้มากสุด 3 เล่ม หรือจำนวนที่ว่าง
            print(f"\n📊 สามารถยืมได้มากสุด {max_borrow} เล่ม")

            quantity_input = input(f"❓ ต้องการยืมกี่เล่ม? (1-{max_borrow}): ").strip()

            try:
                borrow_quantity = int(quantity_input)
                if borrow_quantity < 1 or borrow_quantity > max_borrow:
                    print(f"\n❌ กรุณากรอกจำนวน 1-{max_borrow} เล่มเท่านั้น")
                    return
            except ValueError:
                print("\n❌ กรุณากรอกตัวเลขที่ถูกต้อง")
                return

            # แสดงข้อมูลที่จะยืม
            print("\n" + "─" * 60)
            print("📋 ข้อมูลที่จะยืม:")
            print("─" * 60)
            print(f"👤 ผู้ยืม: {self._decode_string(member[1])}")
            print(f"🆔 ID สมาชิก: {member_id}")
            print(f"📖 หนังสือ: {selected_title}")
            print(f"✍️  ผู้แต่ง: {selected_author}")
            print(f"📚 จำนวนที่ยืม: {borrow_quantity} เล่ม")
            
            confirm = input("\n❓ ยืนยันการยืมหนังสือ? (y/N): ").strip().lower()
            if confirm != 'y':
                print("\n❌ ยกเลิกการยืมหนังสือ")
                return

            # ทำการยืม
            borrow_date = datetime.date.today()
            borrow_date_str = borrow_date.strftime("%Y-%m-%d")
            due_date = borrow_date + datetime.timedelta(days=7)
            due_date_str = due_date.strftime("%Y-%m-%d")

            # สร้างรายการยืมสำหรับแต่ละเล่ม
            borrow_ids = []
            for i in range(borrow_quantity):
                borrow_id = self._get_next_id(self.borrows_file, self.borrow_size)
                borrow_ids.append(borrow_id)

                borrow_data = struct.pack(
                    self.borrow_format,
                    self._encode_string(borrow_id, 4),
                    self._encode_string(selected_book_id, 4),
                    self._encode_string(member_id, 4),
                    self._encode_string(borrow_date_str, 10),
                    self._encode_string("", 10),
                    b'B',
                    b'0'
                )

                with open(self.borrows_file, 'ab') as f:
                    f.write(borrow_data)

            print("\n" + "=" * 60)
            print("✅ ยืมหนังสือสำเร็จ!")
            print("=" * 60)
            print(f"👤 ผู้ยืม: {self._decode_string(member[1])}")
            print(f"🆔 ID สมาชิก: {member_id}")
            print(f"📖 หนังสือ: {selected_title}")
            print(f"✍️  ผู้แต่ง: {selected_author}")
            print(f"📚 จำนวนที่ยืม: {borrow_quantity} เล่ม")
            print(f"📅 วันที่ยืม: {borrow_date_str}")
            print(f"⏰ กำหนดคืน: {due_date_str}")
            
            print(f"\n📋 รายการยืม:")
            for i, borrow_id in enumerate(borrow_ids, 1):
                print(f"  {i}. รหัสรายการยืม: {borrow_id}")

            print("\n⚠️  หมายเหตุสำคัญ:")
            print("• กรุณาคืนหนังสือภายใน 7 วัน")
            print("• หากเกินกำหนดคืน ID จะถูกแบนอัตโนมัติ")
            print("• ID ที่ถูกแบนจะไม่สามารถยืมหนังสือได้จนกว่าจะคืนหนังสือ")
            print("• สามารถคืนหนังสือทีละเล่มหรือทั้งหมดพร้อมกันได้")
            print("=" * 60)

            self.operation_history.append(
                f"{datetime.datetime.now()}: ยืมหนังสือ '{selected_title}' {borrow_quantity} เล่ม (รหัส: {', '.join(borrow_ids)}) โดยสมาชิก ID: {member_id}"
            )

        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")

    def return_book(self):
        print("\n=== คืนหนังสือ ===")
        try:
            member_id = input("กรอก ID สมาชิก: ").strip()

            member = self._find_member_by_id(member_id)
            if not member:
                print("ไม่พบสมาชิก")
                return

            # แสดงรายการหนังสือที่สมาชิกยืมอยู่
            active_borrows = self._get_member_active_borrows(member_id)
            if not active_borrows:
                print("ไม่พบหนังสือที่ยืมอยู่")
                return

            # จัดกลุ่มรายการยืมตามหนังสือ
            book_borrow_groups = {}
            for borrow_id, book_id, borrow_date_str in active_borrows:
                if book_id not in book_borrow_groups:
                    book_borrow_groups[book_id] = []
                book_borrow_groups[book_id].append((borrow_id, borrow_date_str))

            print(f"\n📚 รายการหนังสือที่ยืมอยู่ของ: {self._decode_string(member[1])}")
            print("-" * 100)
            print(f"{'ลำดับ':<4} | {'ชื่อหนังสือ':<34} | {'จำนวน':<9} | {'วันที่ยืม':<16} | {'กำหนดคืน':<12}")
            print("-" * 100)

            book_list = []
            for idx, (book_id, borrow_list) in enumerate(book_borrow_groups.items(), 1):
                book = self._find_book_by_id(book_id)
                book_title = self._decode_string(book[1]) if book else "ไม่พบข้อมูล"
                borrow_count = len(borrow_list)
                borrow_date_str = borrow_list[0][1]  # ใช้วันที่ยืมของเล่มแรก
                
                book_list.append((book_id, borrow_list, book_title))
                print(f"{idx:<4} | {book_title:<30} | {borrow_count:>5} เล่ม | {borrow_date_str:<12} | {borrow_date_str:<12}")

            # เลือกหนังสือที่จะคืน
            print("\nเลือกหนังสือที่จะคืน:")
            choice = input("กรอกลำดับหนังสือ (1-{}): ".format(len(book_list))).strip()

            try:
                choice_idx = int(choice) - 1
                if choice_idx < 0 or choice_idx >= len(book_list):
                    print("กรุณาเลือกลำดับที่ถูกต้อง")
                    return
            except ValueError:
                print("กรุณากรอกตัวเลขที่ถูกต้อง")
                return

            selected_book_id, selected_borrow_list, book_title = book_list[choice_idx]
            
            # ถามว่าจะคืนกี่เล่ม
            print(f"\nเลือกจำนวนที่จะคืน:")
            print(f"หนังสือ: {book_title}")
            print(f"จำนวนที่ยืมอยู่: {len(selected_borrow_list)} เล่ม")
            
            return_choice = input(f"คืนกี่เล่ม? (1-{len(selected_borrow_list)} หรือ 'all' สำหรับทั้งหมด): ").strip().lower()
            
            if return_choice == 'all':
                return_count = len(selected_borrow_list)
            else:
                try:
                    return_count = int(return_choice)
                    if return_count < 1 or return_count > len(selected_borrow_list):
                        print("กรุณากรอกจำนวนที่ถูกต้อง")
                        return
                except ValueError:
                    print("กรุณากรอกตัวเลขที่ถูกต้อง")
                    return

            # คืนหนังสือ
            return_date = datetime.date.today()
            return_date_str = return_date.strftime("%Y-%m-%d")

            borrow_date_str = selected_borrow_list[0][1]  # ใช้วันที่ยืมของเล่มแรก
            borrow_date = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
            due_date = borrow_date + datetime.timedelta(days=7)
            days_overdue = (return_date - due_date).days

            # อัปเดตรายการยืมที่เลือก
            returned_borrow_ids = []
            for i in range(return_count):
                borrow_id = selected_borrow_list[i][0]
                returned_borrow_ids.append(borrow_id)
                
                borrow_index = self._find_borrow_index_by_id(borrow_id)
                if borrow_index != -1:
                    borrow = self._get_borrow_by_index(borrow_index)
                    if borrow:
                        updated_borrow = struct.pack(
                            self.borrow_format,
                            borrow[0],
                            borrow[1],
                            borrow[2],
                            borrow[3],
                            self._encode_string(return_date_str, 10),
                            b'R',
                            borrow[6]
                        )
                        self._update_record(self.borrows_file, borrow_index, updated_borrow, self.borrow_size)

            print("\n" + "=" * 60)
            print("✓ คืนหนังสือเรียบร้อย")
            print("=" * 60)
            print(f"หนังสือ: {book_title}")
            print(f"ผู้ยืม: {self._decode_string(member[1])}")
            print(f"ID สมาชิก: {member_id}")
            print(f"จำนวนที่คืน: {return_count} เล่ม")
            print(f"วันที่ยืม: {borrow_date_str}")
            print(f"กำหนดคืน: {due_date.strftime('%Y-%m-%d')}")
            print(f"วันที่คืน: {return_date_str}")
            
            print(f"\n📋 รายการที่คืน:")
            for i, borrow_id in enumerate(returned_borrow_ids, 1):
                print(f"  {i}. รหัสรายการยืม: {borrow_id}")

            if days_overdue > 0:
                print(f"\n🔴 เกินกำหนด: {days_overdue} วัน")
            elif days_overdue == 0:
                print(f"\n✓ คืนตรงเวลา (วันสุดท้าย)")
            else:
                print(f"\n✓ คืนก่อนกำหนด {abs(days_overdue)} วัน")

            # ตรวจสอบว่ายังมีหนังสือค้างอยู่หรือไม่
            remaining_borrows = self._get_member_active_borrows(member_id)
            has_overdue = False
            for borrow_id, book_id, borrow_date_str in remaining_borrows:
                borrow_date_temp = datetime.datetime.strptime(borrow_date_str, "%Y-%m-%d").date()
                due_date_temp = borrow_date_temp + datetime.timedelta(days=7)
                if (return_date - due_date_temp).days > 0:
                    has_overdue = True
                    break

            # ยกเลิกการแบนหากไม่มีหนังสือค้างและเกินกำหนด
            if not has_overdue and member and member[5] == b'S':
                member_index = self._find_member_index_by_id(member_id)
                if member_index != -1:
                    unban_member = struct.pack(
                        self.member_format,
                        member[0], member[1], member[2], member[3], member[4],
                        b'A',
                        member[6]
                    )
                    self._update_record(self.members_file, member_index, unban_member, self.member_size)
                    print("\n✓ ยกเลิกการแบน ID สมาชิกเรียบร้อย")
                    print("  สามารถยืมหนังสือได้ตามปกติ")

            print("=" * 60)

            self.operation_history.append(f"{datetime.datetime.now()}: คืนหนังสือ '{book_title}' {return_count} เล่ม (รหัส: {', '.join(returned_borrow_ids)}) โดยสมาชิก ID: {member_id}")

        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")

    def view_borrows(self):
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
        borrow_id = input("กรอก ID รายการยืม: ").strip()
        borrow = self._find_borrow_by_id(borrow_id)

        if borrow:
            self._display_borrow(borrow)
        else:
            print("ไม่พบรายการยืม")

    def _view_all_borrows(self):
        borrows = self._get_all_borrows()
        active_borrows = [borrow for borrow in borrows if borrow[6] == b'0']

        if not active_borrows:
            print("\n" + "=" * 60)
            print("📋 รายการยืมทั้งหมด (All Borrow Records)")
            print("=" * 60)
            print("❌ ไม่มีรายการยืมในระบบ")
            print("=" * 60)
            return

        # Count different types of borrows
        current_borrows = [borrow for borrow in active_borrows if borrow[5] == b'B']
        returned_borrows = [borrow for borrow in active_borrows if borrow[5] == b'R']

        print("\n" + "=" * 96)
        print("📋 รายการยืมทั้งหมด (All Borrow Records)")
        print("=" * 96)
        print(f"📊 สรุปข้อมูล:")
        print(f"  • รายการยืมทั้งหมด: {len(active_borrows)} รายการ")
        print(f"  • กำลังยืมอยู่: {len(current_borrows)} รายการ")
        print(f"  • คืนแล้ว: {len(returned_borrows)} รายการ")
        print("=" * 96)
        print("📝 รายละเอียดรายการยืม:")
        print("-" * 96)
        print(f"| {'Borrow ID':<6} | {'Title':<25} | {'Member name':<15} | {'Member id':<8} | {'Borrow date':<10} | {'Status':<10}")
        print("-" * 96)

        for borrow in active_borrows:
            self._display_borrow(borrow, compact=True)

        print("-" * 96)
        print("📅 ข้อมูลอัปเดตล่าสุด:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 96)

    def _view_active_borrows(self):
        borrows = self._get_all_borrows()
        active_borrows = [borrow for borrow in borrows if borrow[5] == b'B' and borrow[6] == b'0']

        if not active_borrows:
            print("ไม่มีหนังสือที่ยืมอยู่")
            return

        # Group borrows by book and member
        book_member_groups = {}
        for borrow in active_borrows:
            book_id = self._decode_string(borrow[1])
            member_id = self._decode_string(borrow[2])
            key = (book_id, member_id)
            if key not in book_member_groups:
                book_member_groups[key] = []
            book_member_groups[key].append(borrow)

        print(f"\nมีหนังสือที่ยืมอยู่ {len(active_borrows)} รายการ")
        print(f"จำนวนหนังสือที่ถูกยืม: {len(active_borrows)} เล่ม")
        print("-" * 110)

        for (book_id, member_id), borrow_list in book_member_groups.items():
            # ใช้ข้อมูลจาก borrow แรก
            borrow = borrow_list[0]
            book = self._find_book_by_id(book_id)
            member = self._find_member_by_id(member_id)
            
            book_title = self._decode_string(book[1]) if book else f"Book ID: {book_id}"
            member_name = self._decode_string(member[1]) if member else f"Member ID: {member_id}"
            
            borrow_date_str = self._decode_string(borrow[3])
            borrow_count = len(borrow_list)
            
            print(f"หนังสือ: {book_title}")
            print(f"ผู้ยืม: {member_name} (ID: {member_id})")
            print(f"จำนวนที่ยืม: {borrow_count} เล่ม")
            print(f"วันที่ยืม: {borrow_date_str}")
            print(f"รหัสรายการยืม: {', '.join([self._decode_string(b[0]) for b in borrow_list])}")
            print("-" * 110)

    def _view_member_borrow_history(self):
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

        overdue_list.sort(key=lambda x: x[1], reverse=True)

        print(f"\n🔴 พบรายการเกินกำหนด {len(overdue_list)} รายการ")
        print("=" * 110)

        for idx, (borrow, days_overdue) in enumerate(overdue_list, 1):
            book_id = self._decode_string(borrow[1])
            member_id = self._decode_string(borrow[2])
            book = self._find_book_by_id(book_id)
            member = self._find_member_by_id(member_id)

            book_quantity = ""
            if book:
                try:
                    quantity_str = self._decode_string(book[5])
                    quantity = int(quantity_str)
                    book_quantity = f" (จำนวน: {quantity} เล่ม)"
                except:
                    book_quantity = " (จำนวน: 1 เล่ม)"
            
            print(f"\n{idx}. หนังสือ: {self._decode_string(book[1]) if book else 'N/A'}{book_quantity}")
            print(f"   ผู้ยืม: {self._decode_string(member[1]) if member else 'N/A'} (ID: {member_id})")
            print(f"   วันที่ยืม: {self._decode_string(borrow[3])}")
            borrow_date = datetime.datetime.strptime(self._decode_string(borrow[3]), "%Y-%m-%d").date()
            due_date = borrow_date + datetime.timedelta(days=7)
            print(f"   กำหนดคืน: {due_date.strftime('%Y-%m-%d')}")
            print(f"   🔴 เกินกำหนด: {days_overdue} วัน")
            print("-" * 110)

    def _find_borrow_by_id(self, borrow_id: str):
        borrows = self._get_all_borrows()
        for borrow in borrows:
            if self._decode_string(borrow[0]) == borrow_id and borrow[6] == b'0':
                return borrow
        return None

    def _find_active_borrow_by_book_id(self, book_id: str):
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
        borrow_id = self._decode_string(borrow[0])
        book_id = self._decode_string(borrow[1])
        member_id = self._decode_string(borrow[2])
        borrow_date_str = self._decode_string(borrow[3])
        return_date = self._decode_string(borrow[4]) or "ยังไม่คืน"
        status = "ยืมอยู่" if borrow[5] == b'B' else "คืนแล้ว"

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
        if book:
            try:
                quantity_str = self._decode_string(book[5])
                quantity = int(quantity_str)
                book_title += f" ({quantity} เล่ม)"
            except:
                book_title += " (1 เล่ม)"
        
        member_name = self._decode_string(member[1]) if member else f"Member ID: {member_id}"

        if compact:
            print(f"ID: {borrow_id} | {book_title[:25]:<25} | {member_name[:15]:<15} | ID:{member_id} | {borrow_date_str} | {status}{overdue_info}")
        else:
            print("\n" + "=" * 60)
            print("📋 ข้อมูลรายการยืม")
            print("=" * 60)
            print(f"🔢 รหัสการยืม    : {borrow_id}")
            print(f"📚 หนังสือ       : {book_title}")
            print(f"👤 ผู้ยืม        : {member_name}")
            print(f"🆔 ID สมาชิก     : {member_id}")
            print(f"📅 วันที่ยืม     : {borrow_date_str}")
            print(f"⏰ กำหนดคืน      : {due_date_str}")
            print(f"📤 วันที่คืน     : {return_date}")
            print(f"📊 สถานะ        : {status}{overdue_info}")
            print("=" * 60)

    def _update_book_status(self, book_id: str, status: bytes):
        book_index = self._find_book_index_by_id(book_id)
        if book_index == -1:
            return

        book = self._get_book_by_index(book_index)
        if not book:
            return

        updated_book = struct.pack(
            self.book_format,
            book[0], book[1], book[2], book[3], book[4], book[5],
            status,
            book[7]
        )

        self._update_record(self.books_file, book_index, updated_book, self.book_size)

    def _get_available_books_for_borrow(self):
        """Get list of books available for borrowing with their available quantities"""
        books = self._get_all_books()
        available_books = []
        
        for book in books:
            if book[7] == b'0':  # Not deleted
                book_id = self._decode_string(book[0])
                title = self._decode_string(book[1])
                author = self._decode_string(book[2])
                
                # Calculate available quantity
                try:
                    total_quantity = int(self._decode_string(book[5]))
                except:
                    total_quantity = 1  # fallback for old records
                
                borrowed_quantity = self._get_borrowed_quantity(book_id)
                available_quantity = total_quantity - borrowed_quantity
                
                if available_quantity > 0:
                    available_books.append((book_id, title, author, available_quantity, total_quantity, borrowed_quantity))
        
        return available_books

    def _get_borrowed_quantity(self, book_id):
        """Get the total quantity of a book that is currently borrowed"""
        borrows = self._get_all_borrows()
        borrowed_quantity = 0
        
        for borrow in borrows:
            if (borrow[6] == b'0' and  # Not deleted
                borrow[5] == b'B' and  # Still borrowed
                self._decode_string(borrow[1]) == book_id):
                # For now, we assume each borrow record represents 1 book
                # In the future, we could add quantity to borrow records
                borrowed_quantity += 1
        
        return borrowed_quantity

    def _update_book_borrowed_quantity(self, book_id, borrow_quantity):
        """Update book status when borrowing (this is a placeholder for now)"""
        # For now, we don't need to update book status since we track borrowing
        # through the borrow records. In the future, we could add a "borrowed_quantity"
        # field to book records.
        pass

    def _get_member_active_borrows(self, member_id):
        """Get list of active borrows for a member"""
        borrows = self._get_all_borrows()
        active_borrows = []
        
        for borrow in borrows:
            if (borrow[6] == b'0' and  # Not deleted
                borrow[5] == b'B' and  # Still borrowed
                self._decode_string(borrow[2]) == member_id):  # Same member
                
                borrow_id = self._decode_string(borrow[0])
                book_id = self._decode_string(borrow[1])
                borrow_date_str = self._decode_string(borrow[3])
                
                active_borrows.append((borrow_id, book_id, borrow_date_str))
        
        return active_borrows

    def delete_borrow(self):
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
        print("\n" + "=" * 60)
        print("📊 สถิติโดยสรุป (Summary Statistics)")
        print("=" * 60)

        books = self._get_all_books()
        active_books = [book for book in books if book[7] == b'0']  # Updated index for deleted flag
        available_books = [book for book in active_books if book[6] == b'A']  # Updated index for status
        borrowed_books = [book for book in active_books if book[6] == b'B']   # Updated index for status
        deleted_books = [book for book in books if book[7] == b'1']  # Updated index for deleted flag

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

        # Calculate total quantities
        total_quantity = 0
        available_quantity = 0
        borrowed_quantity = 0
        
        for book in active_books:
            try:
                quantity = int(self._decode_string(book[5]))
                total_quantity += quantity
                if book[6] == b'A':
                    available_quantity += quantity
                elif book[6] == b'B':
                    borrowed_quantity += quantity
            except:
                total_quantity += 1
                if book[6] == b'A':
                    available_quantity += 1
                elif book[6] == b'B':
                    borrowed_quantity += 1

        # 📚 สถิติหนังสือ
        print("\n📚 สถิติหนังสือ (Book Statistics)")
        print("-" * 50)
        print(f"  📖 รายการหนังสือทั้งหมด: {len(active_books):>3} รายการ")
        print(f"  📚 จำนวนหนังสือรวม:     {total_quantity:>3} เล่ม")
        print(f"  ✅ หนังสือว่าง:          {len(available_books):>3} รายการ ({available_quantity:>3} เล่ม)")
        print(f"  🔄 หนังสือถูกยืม:        {len(borrowed_books):>3} รายการ ({borrowed_quantity:>3} เล่ม)")
        print(f"  🗑️  หนังสือที่ถูกลบ:      {len(deleted_books):>3} รายการ")

        # 👥 สถิติสมาชิก
        print("\n👥 สถิติสมาชิก (Member Statistics)")
        print("-" * 50)
        print(f"  👤 สมาชิกทั้งหมด:        {len(active_members):>3} คน")
        print(f"  ✅ สมาชิกปกติ:           {len(active_members):>3} คน")
        print(f"  🚫 สมาชิกถูกแบน:         {len(banned_members):>3} คน")
        print(f"  🗑️  สมาชิกที่ถูกลบ:       {len(deleted_members):>3} คน")

        # 📋 สถิติการยืม
        print("\n📋 สถิติการยืม (Borrow Statistics)")
        print("-" * 50)
        print(f"  📝 รายการยืมทั้งหมด:     {len(active_borrows):>3} รายการ")
        print(f"  🔄 กำลังยืมอยู่:         {len(current_borrows):>3} รายการ")
        print(f"  ⏰ เกินกำหนดคืน:         {overdue_count:>3} รายการ")
        print(f"  ✅ คืนแล้ว:             {len(returned_borrows):>3} รายการ")
        print(f"  🗑️  รายการที่ถูกลบ:       {len(deleted_borrows):>3} รายการ")

        # 📈 สรุปภาพรวม
        print("\n📈 สรุปภาพรวม (Overall Summary)")
        print("-" * 50)
        print(f"  📊 อัตราการยืม:         {(len(current_borrows)/len(active_borrows)*100):>5.1f}%" if active_borrows else "  📊 อัตราการยืม:           0.0%")
        print(f"  📊 อัตราการคืน:         {(len(returned_borrows)/len(active_borrows)*100):>5.1f}%" if active_borrows else "  📊 อัตราการคืน:           0.0%")
        print(f"  📊 อัตราการเกินกำหนด:    {(overdue_count/len(current_borrows)*100):>5.1f}%" if current_borrows else "  📊 อัตราการเกินกำหนด:      0.0%")
        print(f"  📊 อัตราการใช้งานหนังสือ: {(borrowed_quantity/total_quantity*100):>5.1f}%" if total_quantity else "  📊 อัตราการใช้งานหนังสือ:   0.0%")

        print("\n" + "=" * 60)
        print("📅 ข้อมูลอัปเดตล่าสุด:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)

    def generate_report(self):
        print("\n=== สร้างรายงาน ===")

        try:
            report_content = []
            current_time = datetime.datetime.now()
            current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            timezone_str = current_time.strftime("%z")
            if not timezone_str:
                timezone_str = "+07:00"  # Default to Thailand timezone

            # System Information Section
            report_content.append("Library Borrow System")
            report_content.append("")
            report_content.append(f"Generated At: {current_time_str} ({timezone_str})")
            report_content.append("App Version: 1.0")
            report_content.append("Encoding: UTF-8")
            report_content.append("")

            # Get data
            books = self._get_all_books()
            active_books = [book for book in books if book[7] == b'0']
            
            members = self._get_all_members()
            active_members = [member for member in members if member[6] == b'0' and member[5] == b'A']
            banned_members = [member for member in members if member[6] == b'0' and member[5] == b'S']

            borrows = self._get_all_borrows()
            active_borrows = [borrow for borrow in borrows if borrow[6] == b'0']
            current_borrows = [borrow for borrow in active_borrows if borrow[5] == b'B']
            returned_borrows = [borrow for borrow in active_borrows if borrow[5] == b'R']

            # Borrow Records Table
            report_content.append("Borrow Records")
            report_content.append("-" * 123)
            report_content.append("| ID    | Name     | Phone        | Email              | Title           | Borrow Date | Return Date | Status    | Banned |")
            report_content.append("-" * 123)

            # Display individual borrow records (not grouped)
            for borrow in active_borrows:
                member_id = self._decode_string(borrow[2])
                book_id = self._decode_string(borrow[1])
                member = self._find_member_by_id(member_id)
                book = self._find_book_by_id(book_id)
                
                if member and book:
                    member_name = self._decode_string(member[1])
                    member_phone = self._decode_string(member[3])
                    member_email = self._decode_string(member[2])
                    book_title = self._decode_string(book[1])
                    
                    try:
                        book_quantity = int(self._decode_string(book[5]))
                    except:
                        book_quantity = 1
                    
                    borrow_date_str = self._decode_string(borrow[3])
                    return_date_str = self._decode_string(borrow[4]) if borrow[4] else "-"
                    status = "Borrowed" if borrow[5] == b'B' else "Returned"
                    banned_status = "yes" if member[5] == b'S' else "no"
                    
                    # Format the line to match the table structure
                    line = f"{member_id:<4} | {member_name[:8]:<8} | {member_phone:<12} | {member_email[:18]:<18} | {book_title[:18]:<18} | {borrow_date_str:<11} | {return_date_str:<11} | {status:<9} | {banned_status}"
                    report_content.append(line)

            report_content.append("")

            # Summary Section
            report_content.append("Summary")
            report_content.append("")
            report_content.append(f"Total Borrows (records): {len(active_borrows)}")
            report_content.append(f"Currently Borrowed: {len(current_borrows)}")
            report_content.append(f"Returned: {len(returned_borrows)}")
            report_content.append(f"Banned Members: {len(banned_members)}")
            report_content.append("")
            report_content.append("Members by Status:")
            report_content.append(f"  Active Borrowers: {len(active_members)}")
            report_content.append(f"  Banned Borrowers: {len(banned_members)}")
            report_content.append("")

            # Recent Activities Section
            report_content.append("Recent Activities (last 5)")
            report_content.append("")
            
            # Get recent activities from operation history
            if self.operation_history:
                recent_activities = self.operation_history[-5:]
                for activity in reversed(recent_activities):  # Show most recent first
                    report_content.append(f"{activity}")
            else:
                # Generate some sample activities based on current data
                sample_activities = []
                for borrow in current_borrows[:3]:  # Show up to 3 current borrows
                    member_id = self._decode_string(borrow[2])
                    book_id = self._decode_string(borrow[1])
                    book = self._find_book_by_id(book_id)
                    if book:
                        book_title = self._decode_string(book[1])
                        borrow_date_str = self._decode_string(borrow[3])
                        sample_activities.append(f"{borrow_date_str} 08:41:47: Borrowed \"{book_title}\" ID: {member_id}")
                
                # Add overdue detection if there are banned members
                if banned_members:
                    sample_activities.append(f"{current_time_str}: Overdue detected -> Member ID: {self._decode_string(banned_members[0][0])} (Banned)")
                
                # Add system update
                sample_activities.append(f"{current_time_str}: System update report generated")
                
                for activity in sample_activities[-5:]:  # Show last 5
                    report_content.append(activity)

            report_content.append("")
            report_content.append("End of Report")

            # Write to file
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
        print("\n" + "=" * 70)
        print(" " * 25 + "🏛️ ระบบจัดการห้องสมุด 🏛️")
        print(" " * 20 + "Library Management System v1.0")
        print("=" * 70)
        print("\n📋 เมนูหลัก:")
        print(" ")
        print("─" * 70)
        print("1. 📚 จัดการหนังสือ (Books Management)")
        print("2. 👥 จัดการสมาชิก (Members Management)")
        print("3. 📖 จัดการการยืม-คืน (Borrow/Return Management)")
        print("4. 📊 ดูสถิติโดยสรุป (Statistics)")
        print("5. 📄 สร้างรายงาน (Generate Report)")
        print("0. 🚪 ออกจากระบบ (Exit)")
        print("─" * 70)

    def show_book_menu(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "📚 เมนูจัดการหนังสือ 📚")
        print("=" * 60)
        print("\n📋 เลือกการดำเนินการ:")
        print("─" * 60)
        print("1. ➕ เพิ่มหนังสือ (Add Book)")
        print("2. 👁️  ดูข้อมูลหนังสือ (View Books)")
        print("3. ✏️  แก้ไขหนังสือ (Update Book)")
        print("4. 🗑️ ลบหนังสือ (Delete Book)")
        print("0. 🔙 กลับเมนูหลัก")
        print("─" * 60)

    def show_member_menu(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "👥 เมนูจัดการสมาชิก 👥")
        print("=" * 60)
        print("\n📋 เลือกการดำเนินการ:")
        print("─" * 60)
        print("1. ➕ เพิ่มสมาชิก (Add Member)")
        print("2. 👁️  ดูข้อมูลสมาชิก (View Members)")
        print("3. ✏️  แก้ไขสมาชิก (Update Member)")
        print("4. 🗑️ ลบสมาชิก (Delete Member)")
        print("0. 🔙 กลับเมนูหลัก")
        print("─" * 60)

    def show_borrow_menu(self):
        print("\n" + "=" * 60)
        print(" " * 20 + "📖 เมนูจัดการการยืม-คืน 📖")
        print("=" * 60)
        print("\n📋 เลือกการดำเนินการ:")
        print("─" * 60)
        print("1. 📚 ยืมหนังสือ (Borrow Book)")
        print("2. 🔄 คืนหนังสือ (Return Book)")
        print("3. 👁️  ดูรายการยืม (View Borrows)")
        print("4. 🗑️ ลบรายการยืม (Delete Borrow)")
        print("0. 🔙 กลับเมนูหลัก")
        print("─" * 60)

    def run(self):

        while True:
            try:
                self.show_main_menu()
                choice = input("\n❓ เลือกเมนู (0-5): ").strip()

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
                    print("\n" + "=" * 60)
                    print(" " * 20 + "🙏 ขอบคุณที่ใช้บริการ! 🙏")
                    print(" " * 15 + "Thank you for using our service!")
                    print("=" * 60)
                    break
                else:
                    print("\n❌ กรุณาเลือกเมนูที่ถูกต้อง (0-5)")
                    input("กด Enter เพื่อดำเนินการต่อ...")

            except KeyboardInterrupt:
                print("\n\n⚠️ ระบบถูกปิดโดยผู้ใช้")
                print("🙏 ขอบคุณที่ใช้บริการ!")
                break
            except Exception as e:
                print(f"\n❌ เกิดข้อผิดพลาด: {e}")
                input("กด Enter เพื่อดำเนินการต่อ...")

    def _handle_book_menu(self):
        while True:
            self.show_book_menu()
            choice = input("\n❓ เลือก (0-4): ").strip()

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
                print("\n❌ กรุณาเลือกเมนูที่ถูกต้อง (0-4)")
                input("กด Enter เพื่อดำเนินการต่อ...")

    def _handle_member_menu(self):
        while True:
            self.show_member_menu()
            choice = input("\n❓ เลือก (0-4): ").strip()

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
                print("\n❌ กรุณาเลือกเมนูที่ถูกต้อง (0-4)")
                input("กด Enter เพื่อดำเนินการต่อ...")

    def _handle_borrow_menu(self):
        while True:
            self.show_borrow_menu()
            choice = input("\n❓ เลือก (0-4): ").strip()

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
                print("\n❌ กรุณาเลือกเมนูที่ถูกต้อง (0-4)")
                input("กด Enter เพื่อดำเนินการต่อ...")

