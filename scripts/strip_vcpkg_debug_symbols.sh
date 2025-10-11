#!/bin/bash

# A script to strip unnecessary debug symbols from vcpkg-generated debug libraries.
# This is useful for reducing artifact cache sizes in CI/CD environments.

set -euo pipefail # Exit on error, undefined variable, or pipe failure

# --- Functions ---

usage() {
    echo "Strips debug symbols from libraries in a vcpkg packages directory."
    echo ""
    echo "Usage: $0 <path_to_vcpkg_packages_directory>"
    echo ""
    echo "Example: $0 ./vcpkg/packages"
    exit 1
}

# --- Pre-flight Checks ---

if ! command -v strip &> /dev/null; then
    echo "Error: 'strip' command not found. Please ensure binutils is installed." >&2
    exit 1
fi

if [ "$#" -ne 1 ]; then
    echo "Error: Invalid number of arguments." >&2
    usage
fi

PACKAGES_DIR="$1"

if [ ! -d "$PACKAGES_DIR" ]; then
    echo "Error: Directory not found at '$PACKAGES_DIR'" >&2
    exit 1
fi

# --- Main Logic ---

echo "Target directory: $(realpath "$PACKAGES_DIR")"
echo "Searching for debug libraries to strip..."
echo ""

# Find all static libraries (.a) and shared objects (.so, .so.*)
find "$PACKAGES_DIR" -type f \( -path "*/debug/lib/*.a" -o -path "*/debug/lib/*.so" -o -path "*/debug/lib/*.so.*" \) -print0 | \
    xargs -0 -I {} sh -c 'echo "Stripping: {}"; strip --strip-debug "{}"'

echo ""
echo "Stripping complete."
