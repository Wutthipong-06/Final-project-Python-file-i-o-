#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the fix works
"""

import os
import struct

def test_data_migration():
    """Test the data migration functionality"""
    
    print("=== Testing Data Migration ===")
    
    # Check if books.dat exists
    if os.path.exists('books.dat'):
        file_size = os.path.getsize('books.dat')
        print(f"books.dat exists, size: {file_size} bytes")
        
        # Check if it's divisible by new size (184 bytes)
        new_size = struct.calcsize('4s100s50s20s4s4s1s1s')
        old_size = struct.calcsize('4s100s50s20s4s1s1s')
        
        print(f"New record size: {new_size} bytes")
        print(f"Old record size: {old_size} bytes")
        
        if file_size % new_size == 0:
            print("✓ Data is already in new format")
            return True
        elif file_size % old_size == 0:
            print("⚠ Data is in old format, needs migration")
            return False
        else:
            print("⚠ Data format is unknown or corrupted")
            return False
    else:
        print("books.dat does not exist")
        return True

def test_library_system():
    """Test the library system initialization"""
    
    print("\n=== Testing Library System ===")
    
    try:
        from libsys import LibrarySystem
        
        print("Creating LibrarySystem instance...")
        library = LibrarySystem()
        print("✓ LibrarySystem created successfully")
        
        print("Testing _get_all_books...")
        books = library._get_all_books()
        print(f"✓ Found {len(books)} books")
        
        print("Testing view_statistics...")
        library.view_statistics()
        print("✓ Statistics displayed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing library system fix...\n")
    
    # Test data migration
    migration_ok = test_data_migration()
    
    # Test library system
    system_ok = test_library_system()
    
    if migration_ok and system_ok:
        print("\n✓ All tests passed! The system should work correctly now.")
    else:
        print("\n⚠ Some tests failed. You may need to reset the data files.")
        print("Run: python reset_library_data.py")
