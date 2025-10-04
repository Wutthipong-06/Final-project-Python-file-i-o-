#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to reset library data files
Use this if you encounter data corruption issues
"""

import os
import shutil

def reset_library_data():
    """Reset all library data files to start fresh"""
    
    print("=== Library Data Reset Tool ===")
    print("This will delete all existing library data files.")
    print("Make sure you have backed up any important data!")
    
    confirm = input("\nAre you sure you want to reset all data? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Reset cancelled.")
        return
    
    # Files to reset
    data_files = [
        'books.dat',
        'members.dat', 
        'borrows.dat',
        'library_report.txt'
    ]
    
    # Backup files to remove
    backup_files = [
        'books.dat.backup',
        'members.dat.backup',
        'borrows.dat.backup'
    ]
    
    print("\nRemoving data files...")
    for filename in data_files:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"  ✓ Removed {filename}")
        else:
            print(f"  - {filename} not found")
    
    print("\nRemoving backup files...")
    for filename in backup_files:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"  ✓ Removed {filename}")
        else:
            print(f"  - {filename} not found")
    
    print("\n✓ Data reset completed!")
    print("You can now run the library system with fresh data.")
    print("Run: python library_system.py")

if __name__ == "__main__":
    reset_library_data()
