#!/usr/bin/env python3
"""
Creates a vcpkg binary cache from vcpkg/packages directory.

Based on vcpkg's binary caching format:
- Source: https://github.com/microsoft/vcpkg-tool/blob/main/src/vcpkg/binarycaching.cpp
- Docs: https://learn.microsoft.com/en-us/vcpkg/reference/binarycaching

Cache format:
- Files provider stores zip archives with hash-based sharding
- Structure: {cache_path}/{abi_hash[:2]}/{abi_hash}.zip
- Each package directory is compressed to a zip file
- ABI hash is calculated as SHA256 of vcpkg_abi_info.txt content
"""

import os
import sys
import zipfile
import hashlib
from pathlib import Path
import argparse
import re

def find_abi_hash(package_dir: Path) -> tuple[str, str]:
    """
    Find the ABI hash for a package.
    
    Returns:
        tuple[str, str]: (port_name, abi_hash)
    
    The ABI hash is calculated as the SHA256 hash of the vcpkg_abi_info.txt 
    file content. Location: {package_dir}/share/{port_name}/vcpkg_abi_info.txt
    
    The port_name is extracted from the package directory name (minus triplet).
    Example: ada-idna_x64-linux -> port_name is "ada-idna"
    """
    share_dir = package_dir / "share"
    
    if not share_dir.exists():
        raise FileNotFoundError(f"No share directory found in {package_dir}")
    
    # Extract port name from package directory (remove triplet suffix)
    # Format: {port}_{triplet} -> extract {port}
    package_name = package_dir.name
    parts = package_name.rsplit('_', 1)
    port_name = parts[0] if len(parts) == 2 else package_name
    
    # Locate the vcpkg_abi_info.txt file
    port_dir = share_dir / port_name
    abi_info_file = port_dir / "vcpkg_abi_info.txt"
    
    if not abi_info_file.exists():
        raise FileNotFoundError(f"Could not find {abi_info_file}")
    
    # Calculate SHA256 hash of the file content
    content = abi_info_file.read_bytes()
    abi_hash = hashlib.sha256(content).hexdigest()
    
    return port_name, abi_hash


def compress_package_to_zip(package_dir: Path, output_zip: Path) -> None:
    """
    Compress a package directory to a zip file.
    
    Uses standard ZIP_DEFLATED compression as per vcpkg's binary cache format.
    All files are stored with paths relative to the package directory root.
    """
    print(f"  Compressing {package_dir.name}...")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add 'followlinks=False' so os.walk reports symlinks instead of following them.
        for root, dirs, files in os.walk(package_dir, followlinks=False):
            
            # This loop is critical for two reasons:
            # 1. It preserves the original permissions of every directory.
            # 2. It ensures that empty directories are explicitly added to the archive.
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                # Store paths relative to package directory
                arcname = dir_path.relative_to(package_dir)
                zip_info = zipfile.ZipInfo(f"{arcname}/")
                zip_info.external_attr = dir_path.lstat().st_mode << 16
                zipf.writestr(zip_info, "")

            for file in files:
                file_path = Path(root) / file
                # Store paths relative to package directory
                arcname = file_path.relative_to(package_dir)
                if file_path.is_symlink():
                    # 1. Create a ZipInfo object for the symlink
                    zip_info = zipfile.ZipInfo(str(arcname))
                    
                    # 2. Set the file attributes by reading the symlink's actual permissions.
                    zip_info.external_attr = file_path.lstat().st_mode << 16
                    
                    # 3. Read the link's target path
                    link_target = os.readlink(file_path)
                    
                    # 4. Write the link target as the "content" of the symlink
                    zipf.writestr(zip_info, link_target)
                else:
                    # This is a regular file. We must explicitly read its permissions
                    # and content to ensure they are preserved.
                    zip_info = zipfile.ZipInfo(str(arcname))
                    zip_info.external_attr = file_path.lstat().st_mode << 16
                    with open(file_path, 'rb') as f:
                        zipf.writestr(zip_info, f.read())
    
    size_mb = output_zip.stat().st_size / 1024 / 1024
    print(f"  Created: {output_zip.relative_to(output_zip.parent.parent)} ({size_mb:.2f} MB)")


def create_cache_from_packages(packages_dir: Path, cache_dir: Path, dry_run: bool = False) -> None:
    """
    Create a vcpkg binary cache from a packages directory.
    
    Cache structure uses hash-based sharding:
    - Format: {cache_dir}/{first_2_hash_chars}/{full_abi_hash}.zip
    - Example: b3e6227a9c... -> b3/b3e6227a9c....zip
    
    Reference: https://learn.microsoft.com/en-us/vcpkg/reference/binarycaching#files
    """
    if not packages_dir.exists():
        print(f"Error: Packages directory not found: {packages_dir}")
        sys.exit(1)
    
    # Get all package directories
    package_dirs = [d for d in packages_dir.iterdir() if d.is_dir()]
    
    if not package_dirs:
        print(f"Error: No package directories found in {packages_dir}")
        sys.exit(1)
    
    print(f"Found {len(package_dirs)} packages")
    print(f"Cache output: {cache_dir}")
    print()
    
    if not dry_run:
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    created = 0
    skipped = 0
    errors = []
    
    for package_dir in sorted(package_dirs):
        try:
            print(f"Processing: {package_dir.name}")
            
            # Find ABI hash for this package
            port_name, abi_hash = find_abi_hash(package_dir)
            print(f"  Port: {port_name}")
            print(f"  ABI Hash: {abi_hash}")
            
            # Create sharded cache path (first 2 chars as subdirectory)
            # vcpkg uses sharding to avoid too many files in one directory
            subdir = cache_dir / abi_hash[:2]
            cache_file = subdir / f"{abi_hash}.zip"
            
            if cache_file.exists() and not dry_run:
                print(f"  Skipped: Cache file already exists at {abi_hash[:2]}/{abi_hash}.zip")
                skipped += 1
                print()
                continue
            
            if dry_run:
                print(f"  Would create: {abi_hash[:2]}/{abi_hash}.zip")
                created += 1
            else:
                # Create subdirectory and compress package
                subdir.mkdir(parents=True, exist_ok=True)
                compress_package_to_zip(package_dir, cache_file)
                created += 1
            
            print()
            
        except Exception as e:
            error_msg = f"Error processing {package_dir.name}: {e}"
            print(f"  ERROR: {e}")
            print()
            errors.append(error_msg)
            continue
    
    # Print summary
    print("=" * 70)
    print("Summary:")
    print(f"  Created: {created}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    if not dry_run and created > 0:
        print(f"\nCache created at: {cache_dir.absolute()}")
        print("\nTo use this cache, set:")
        print(f"  export VCPKG_BINARY_SOURCES='clear;files,{cache_dir.absolute()},readwrite'")


def main():
    parser = argparse.ArgumentParser(
        description='Create vcpkg binary cache from packages directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create cache from default vcpkg/packages directory
  %(prog)s
  
  # Specify custom paths
  %(prog)s -p /path/to/vcpkg/packages -c /path/to/cache
  
  # Dry run (show what would be done)
  %(prog)s --dry-run

References:
  - vcpkg-tool source: https://github.com/microsoft/vcpkg-tool/blob/main/src/vcpkg/binarycaching.cpp
  - Binary caching docs: https://learn.microsoft.com/en-us/vcpkg/reference/binarycaching
        """
    )
    
    parser.add_argument(
        '-p', '--packages-dir',
        type=Path,
        default=Path('vcpkg/packages'),
        help='Path to vcpkg packages directory (default: vcpkg/packages)'
    )
    
    parser.add_argument(
        '-c', '--cache-dir',
        type=Path,
        default=Path('vcpkg-cache'),
        help='Path to output cache directory (default: vcpkg-cache)'
    )
    
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be done without creating files'
    )
    
    args = parser.parse_args()
    
    create_cache_from_packages(args.packages_dir, args.cache_dir, args.dry_run)


if __name__ == '__main__':
    main()
