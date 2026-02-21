import os
import hashlib
import sys
from typing import List


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
def find_duplicates(
    directory: str,
    fuzzy_images: bool = False,
    similarity_threshold: float = 0.80
) -> List[List[str]]:
    """Scan directory recursively and return list of duplicate groups (each a list of file paths)"""
    
    if fuzzy_images:
        try:
            from PIL import Image
            from imagehash import phash
        except ImportError as exc:
            raise ImportError("Fuzzy image detection requires extra dependencies. Install with: pip install psamfinder[fuzzy]") from exc
        
        # collect the image paths
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        image_paths:List[str] = []
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(image_extensions):
                    image_paths.append(os.path.join(root, filename))
        
        if len(image_paths) < 2:
            return []
        
        # convert perceptual hashes, skipping invalid images
        hashes = []
        valid_paths = []
        for path in image_paths:
            try:
                img = Image.open(path)
                h = phash(img)
                hashes.append(h)
                valid_paths.append(path)
            except Exception as e: # pylint: disable=broad-exception-caught
                print(f"Error processing image {path}: {e}", file=sys.stderr)
        
        n = len(hashes)
        if n < 2:
            return []
        
        # Convert similarity to max Hamming distance (for 64=bit pHash)
        hash_size = len(hashes[0].hash.flatten())
        max_distance = int((1 - similarity_threshold) * hash_size)
        
        # Union-find helpers
        parent = list(range(n))
        def find(i: int) -> int:
            if parent[i] != i:
                parent[i] = find(parent[i])
            return parent[i]
        def union(i: int, j: int) -> None:
            pi = find(i)
            pj = find(j)
            if pi != pj:
                parent[pi] = pj
                
        for i in range(n):
            for j in range(i + 1, n):
                dist = hashes[i] - hashes[j] # Hamming distance
                if dist <= max_distance:
                    union(i, j)
        
        # form groups
        from collections import defaultdict
        groups: defaultdict[int, List[str]] = defaultdict(list)
        for i in range(n):
            root = find(i)
            groups[root].append(valid_paths[i])
        
        dupe_groups = [group for group in groups.values() if len(group) > 1]
        # Debug: show pairwise distances for small sets (helps user tune threshold)
        if len(image_paths) <= 20 and dupe_groups:
            print("\nDebug: pairwise distances in duplicate groups:")
            for group in dupe_groups:
                if len(group) == 2:  # only show for pairs (most common during testing)
                    try:
                        h1 = phash(Image.open(group[0]))
                        h2 = phash(Image.open(group[1]))
                        dist = h1 - h2
                        sim = 1 - (dist / 64.0)
                        print(f"  {os.path.basename(group[0])} ↔ {os.path.basename(group[1])} : "
                              f"dist {dist}, sim {sim:.3f}")
                    except Exception as e: # pylint: disable=broad-exception-caught
                        print(f"  Could not compute debug distance for group: {e}")
        return dupe_groups

    else:
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
        dupe_groups = [paths for paths in hash_dict.values() if len(paths) > 1]
        return dupe_groups

# printing duplicates
def print_duplicates(dupe_groups: List[List[str]]) -> None:
    if not dupe_groups:
        print("No duplicates found")
        return
    print("Duplicates found")
    for idx, group in enumerate(dupe_groups, 1):
        print(f"Group {idx}:")
        for path in group:
            print(f" - {path}")
        print()

def delete_duplicates(dupe_groups: List[List[str]], dry_run: bool = False) -> bool: 
    """Prompt the user to delete duplicates, keeping one per group"""
    any_deleted = False
    
    for idx, group in enumerate(dupe_groups, 1):
        print(f"Duplicates group {idx}:")
        for i, path in enumerate(group, 1):
            print(f" {i}. {path}")
        keep = input(f"\nEnter number to keep (1-{len(group)}), or 'skip' to keep all: ").strip()
        
        if keep.lower() == 'skip':
            continue
    

        try:
            keep_idx = int(keep) - 1
            if 0 <= keep_idx < len(group):
                deleted_count = 0
                for i, path in enumerate(group):
                    if i != keep_idx:
                        if dry_run:
                            print(f"Would have deleted: {path}")
                        else:
                            os.remove(path)
                            print(f"Deleted: {path}")
                            deleted_count += 1
                if deleted_count > 0:
                    any_deleted = True
            else:
                print("Invalid choice; skipping")
        except ValueError:
            print("Invalid input; skipping")
    return any_deleted

                    