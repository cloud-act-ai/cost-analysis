#!/usr/bin/env python3
"""
Cleanup script for FinOps360 Cost Analysis project.
This script will remove all files not needed for the new app structure.
"""
import os
import shutil
import sys

def main():
    """Clean up the FinOps360 Cost Analysis project directory."""
    print("Cleaning up FinOps360 Cost Analysis project directory...")
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create backup directory
    backup_dir = os.path.join(base_dir, "backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Files and directories to keep
    keep = [
        "app",
        "run.sh",
        "config.yaml",
        "requirements.txt",
        "README.md",
        "BIGQUERY_INTEGRATION.md",
        "reports",
        "backup",
        "cleanup.py",
        ".git"
    ]
    
    # Get all files and directories in the base directory
    files = os.listdir(base_dir)
    
    # Process each file/directory
    for file in files:
        if file not in keep:
            path = os.path.join(base_dir, file)
            backup_path = os.path.join(backup_dir, file)
            
            print(f"Moving {file} to backup...")
            try:
                # If it's a directory, copy it recursively
                if os.path.isdir(path):
                    shutil.copytree(path, backup_path, dirs_exist_ok=True)
                    shutil.rmtree(path)
                # If it's a file, just copy it
                else:
                    shutil.copy2(path, backup_path)
                    os.remove(path)
            except Exception as e:
                print(f"Error with {file}: {e}")
    
    print("Cleanup complete! All unnecessary files have been moved to the backup directory.")
    print("The app directory now contains only the essential files for the FinOps360 Cost Analysis dashboard.")

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    response = input("This will move all unnecessary files to a backup directory. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cleanup cancelled.")
        sys.exit(0)
    
    main()