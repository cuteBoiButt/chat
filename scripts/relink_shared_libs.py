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

def get_file_stats(filepath):
    """Calculates the size and SHA256 hash of a file."""
    stats = {'size': -1, 'hash': None, 'error': None}
    try:
        stats['size'] = os.path.getsize(filepath)
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        stats['hash'] = sha256.hexdigest()
    except (IOError, OSError) as e:
        stats['error'] = e
    return stats

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

def process_lib_directory(lib_dir, dry_run=False, verbose=False):
    """
    Processes a single 'lib' directory to find and relink duplicate shared libraries.
    """
    print(f"\n--- Processing: {lib_dir}")
    if not os.path.isdir(lib_dir):
        print("  [*] Directory not found. Skipping.")
        return

    try:
        all_files = os.listdir(lib_dir)
    except OSError as e:
        print(f"  [!] Could not read directory {lib_dir}: {e}", file=sys.stderr)
        return

    if verbose:
        print(f"  [V] Files found: {', '.join(all_files) or 'None'}")

    # 1. Group files by their base library name
    lib_groups = defaultdict(list)
    for filename in all_files:
        base_name = get_lib_base_name(filename)
        if base_name:
            lib_groups[base_name].append(filename)

    if not lib_groups:
        print("  [*] No shared libraries found to process. Skipping.")
        return

    # 2. Process each group
    for base_name, files in lib_groups.items():
        if len(files) < 2:
            if verbose:
                print(f"  [V] Group '{base_name}' has only one file. No action needed.")
            continue

        print(f"\n  [+] Found group '{base_name}': {', '.join(sorted(files))}")

        # 3. Identify the canonical file
        files.sort(key=len, reverse=True)
        canonical_file = files[0]
        potential_links = files[1:]
        canonical_path = os.path.join(lib_dir, canonical_file)
        print(f"    -> Canonical file: {canonical_file}")

        if os.path.islink(canonical_path):
            print(f"    [!] Canonical file is a symlink. Skipping this group to be safe.")
            continue

        # 4. Get stats of the canonical file
        canonical_stats = get_file_stats(canonical_path)
        if canonical_stats['error']:
            print(f"    [!] Could not read canonical file: {canonical_stats['error']}. Skipping group.")
            continue

        if verbose:
            print(f"      [V] Size: {canonical_stats['size']} bytes, Hash: {canonical_stats['hash']}")

        # 5. Check each potential link
        for link_name in potential_links:
            link_path = os.path.join(lib_dir, link_name)

            if os.path.islink(link_path):
                msg = f"    - Skipping '{link_name}': Already a symlink"
                if verbose:
                    try:
                        target = os.readlink(link_path)
                        msg += f" -> '{target}'"
                    except OSError:
                        msg += " (broken link?)"
                print(msg)
                continue

            link_stats = get_file_stats(link_path)

            if verbose:
                print(f"    - Checking '{link_name}':")
                if link_stats['error']:
                    print(f"      [V] Could not read file: {link_stats['error']}")
                else:
                    print(f"      [V] Size: {link_stats['size']} bytes, Hash: {link_stats['hash']}")

            # Compare files
            if link_stats['hash'] and link_stats['hash'] == canonical_stats['hash']:
                print(f"    - Found duplicate: '{link_name}' is identical to '{canonical_file}'.")

                if dry_run:
                    print(f"      (DRY RUN) Would remove and link to '{canonical_file}'")
                else:
                    try:
                        print(f"      -> Relinking '{link_name}' -> '{canonical_file}'")
                        os.remove(link_path)
                        os.symlink(canonical_file, link_path)
                    except (IOError, OSError) as e:
                        print(f"      [!] FAILED to relink: {e}", file=sys.stderr)
            else:
                print(f"    - WARNING: '{link_name}' is not identical to the canonical file. Leaving it alone.")


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
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="""Print detailed information during processing, including file sizes,
hashes, and existing symlink targets. Greatly helps in debugging."""
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

    package_dirs = [d for d in os.listdir(args.packages_root)
                    if os.path.isdir(os.path.join(args.packages_root, d))]

    if not package_dirs:
        print(f"No package directories found in '{args.packages_root}'.")
        sys.exit(0)

    print(f"Found {len(package_dirs)} packages. Starting scan...")

    for package_name in sorted(package_dirs):
        package_path = os.path.join(args.packages_root, package_name)
        
        # Define the list of potential library directories to check for each package
        potential_lib_dirs = [
            os.path.join(package_path, 'lib'),
            os.path.join(package_path, 'debug', 'lib')
        ]

        for lib_path in potential_lib_dirs:
            if os.path.isdir(lib_path):
                # If the directory exists, process it
                process_lib_directory(lib_path, args.dry_run, args.verbose)

    print("\n\n=== Script finished. ===")


if __name__ == "__main__":
    main()
