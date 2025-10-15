#!/usr/bin/env python3
import os
import sys
import hashlib
import argparse
from collections import defaultdict

# --- Configuration ---
# Shared library extensions to look for.
LIB_EXTENSIONS = ('.so',)

# --- Helper Functions ---

def get_file_hash(filepath, block_size=65536):
    """Calculates the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()
    except (IOError, OSError) as e:
        print(f"  [!] Error reading file {filepath}: {e}", file=sys.stderr)
        return None

def get_lib_base_name(filename):
    """
    Extracts the base name of a library.
    e.g., 'libfoo.so.1.2.3' -> 'libfoo'
    """
    for ext in LIB_EXTENSIONS:
        if ext in filename:
            return filename.split(ext, 1)[0]
    return None

# --- Core Logic ---

def process_lib_directory(lib_dir, dry_run=False):
    """
    Processes a single 'lib' directory to find and relink duplicate shared libraries.
    """
    print(f"\n--- Processing: {lib_dir}")
    if not os.path.isdir(lib_dir):
        print("  [*] Directory not found. Skipping.")
        return

    # 1. Group files by their base library name
    lib_groups = defaultdict(list)
    for filename in os.listdir(lib_dir):
        if filename.endswith(LIB_EXTENSIONS):
            base_name = get_lib_base_name(filename)
            if base_name:
                lib_groups[base_name].append(filename)

    if not lib_groups:
        print("  [*] No shared libraries found. Skipping.")
        return

    # 2. Process each group
    for base_name, files in lib_groups.items():
        if len(files) < 2:
            continue  # Nothing to do for single files

        print(f"\n  [+] Found group '{base_name}': {', '.join(files)}")

        # 3. Identify the canonical file (longest name is the best heuristic)
        #    and the files that should be links.
        files.sort(key=len, reverse=True)
        canonical_file = files[0]
        potential_links = files[1:]

        canonical_path = os.path.join(lib_dir, canonical_file)
        print(f"    -> Canonical file: {canonical_file}")
        
        # 4. Get the hash of the canonical file
        canonical_hash = get_file_hash(canonical_path)
        if not canonical_hash:
            print(f"    [!] Could not hash canonical file. Skipping group '{base_name}'.")
            continue

        # 5. Check each potential link
        for link_name in potential_links:
            link_path = os.path.join(lib_dir, link_name)

            # A. Skip if it's already a symlink
            if os.path.islink(link_path):
                print(f"    - Skipping '{link_name}': Already a symlink.")
                continue

            # B. Compare hashes to ensure they are identical files
            link_hash = get_file_hash(link_path)
            if link_hash == canonical_hash:
                print(f"    - Found duplicate: '{link_name}' is identical to '{canonical_file}'.")
                
                # C. Perform the replacement
                if dry_run:
                    print(f"      (DRY RUN) Would remove '{link_name}' and link to '{canonical_file}'")
                else:
                    try:
                        print(f"      -> Relinking '{link_name}' -> '{canonical_file}'")
                        os.remove(link_path)
                        # Create a relative symlink, which is more portable
                        os.symlink(canonical_file, link_path)
                    except (IOError, OSError) as e:
                        print(f"      [!] FAILED to relink: {e}", file=sys.stderr)
            else:
                print(f"    - WARNING: '{link_name}' is not identical to '{canonical_file}'. Leaving it alone.")


def main():
    """Main function to parse arguments and start the process."""
    parser = argparse.ArgumentParser(
        description="Finds duplicate shared libraries in a vcpkg/nuget-style cache and replaces them with symlinks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "packages_root",
        help="The root directory containing all the packages (e.g., 'path/to/packages')."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually deleting files or creating symlinks."
    )

    args = parser.parse_args()

    if args.dry_run:
        print("===================================")
        print("===     DRY RUN MODE ACTIVE     ===")
        print("=== No files will be modified.  ===")
        print("===================================")
        
    if not os.path.isdir(args.packages_root):
        print(f"Error: The specified directory does not exist: {args.packages_root}", file=sys.stderr)
        sys.exit(1)

    # Find all package directories inside the root
    package_dirs = [d for d in os.listdir(args.packages_root) 
                    if os.path.isdir(os.path.join(args.packages_root, d))]
    
    if not package_dirs:
        print(f"No package directories found in '{args.packages_root}'.")
        sys.exit(0)

    print(f"Found {len(package_dirs)} packages. Starting scan...")

    for package_name in package_dirs:
        package_path = os.path.join(args.packages_root, package_name)
        lib_path = os.path.join(package_path, 'lib')
        
        if os.path.isdir(lib_path):
            process_lib_directory(lib_path, args.dry_run)

    print("\n\n=== Script finished. ===")


if __name__ == "__main__":
    main()
