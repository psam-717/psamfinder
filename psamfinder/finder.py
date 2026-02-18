import os
import hashlib
import sys


# function for computing hash
def compute_hash(filepath):
    """Compute SHA-256 hash of file content. Returns None on error"""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error hashing {filepath}: {e}", file=sys.stderr)
        return None # for skipping problematic files
    
    

# find duplicates
def find_duplicates(directory):
    """Scan directory recursively and return dict of duplicates"""
    hash_dict: dict[str, list[str]] = {} # {hash: [path]}
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_hash = compute_hash(filepath)
            if file_hash: # only add the file path to the dict if has was successful
                if file_hash not in hash_dict:
                    hash_dict[file_hash] = []
                hash_dict[file_hash].append(filepath)
    # filter duplicates with 2+ files
    duplicates = {h: paths for h, paths in hash_dict.items() if len(paths) > 1}
    return duplicates

# printing duplicates
def print_duplicates(duplicates):
    if not duplicates:
        print("No duplicates found")
        return
    print("Duplicates found")
    for file_hash, paths in duplicates.items():
        print(f"Hash: {file_hash}")
        for path in paths:
            print(f" - {path}")
        print()

def delete_duplicates(duplicates): 
    """Prompt the user to delete duplicates, keeping one per group"""
    for file_hash, paths in duplicates.items():
        print(f"Duplicates for hash {file_hash}")
        for i, path in enumerate(paths, 1):
            print(f" {i}. {path}")
        keep = input("enter number to keep (or 'skip' to keep all): ")
        if keep.lower() == 'skip':
            continue
        try:
            keep_idx = int(keep) - 1
            if 0 <= keep_idx < len(paths):
                for i, path in enumerate(paths):
                    if i != keep_idx:
                        os.remove(path)
                        print(f"Deleted: {path}")
            else:
                print("Invalid choice; skipping")
        except ValueError:
            print("Invalid input; skipping")

                    