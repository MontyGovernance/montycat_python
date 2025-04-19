#!/bin/bash

# Configuration
PACKAGE_NAME="montycat"
VERSION="0.1.35"
# Define multiple source directories and their files
declare -A SOURCE_DIRS
SOURCE_DIRS["montycat/core"]="utils.py"      # Space-separated list of files
SOURCE_DIRS["montycat/store_functions"]="store_generic_functions.py"           # Add more directories as needed
PYPI_TOKEN="${PYPI_TOKEN:-}"

# Exit on any error
set -e

# Check prerequisites and install if missing
check_prerequisites() {
    command -v python3 >/dev/null 2>&1 || { echo "Error: Python3 is required"; exit 1; }
    if python3 -c "import twine" >/dev/null 2>&1; then
        echo "Twine is already available"
    else
        echo "Twine not found, attempting to install..."
        if python3 -m pip --version >/dev/null 2>&1; then
            echo "Installing twine using python3 -m pip..."
            python3 -m pip install --user twine
        elif command -v pip3 >/dev/null 2>&1; then
            echo "Installing twine using pip3..."
            pip3 install --user twine
        elif command -v pip >/dev/null 2>&1; then
            echo "Installing twine using pip..."
            pip install --user twine
        else
            echo "No pip found, attempting to install pip using ensurepip..."
            python3 -m ensurepip
            python3 -m pip install --upgrade pip
            python3 -m pip install --user twine
        fi
        echo "Successfully installed twine"
    fi
}

# Compile multiple Python files to .pyc across multiple directories
compile_file() {
    echo "Compiling Python files across multiple directories..."
    
    if [ ${#SOURCE_DIRS[@]} -eq 0 ]; then
        echo "Error: No source directories specified for compilation"
        exit 1
    fi

    for DIR in "${!SOURCE_DIRS[@]}"; do
        # Convert space-separated file list to array
        IFS=' ' read -r -a FILES <<< "${SOURCE_DIRS[$DIR]}"
        
        if [ ! -d "$DIR" ]; then
            echo "Warning: Directory $DIR not found, skipping..."
            continue
        fi

        for FILE in "${FILES[@]}"; do
            if [ ! -f "$DIR/$FILE" ]; then
                echo "Warning: File $DIR/$FILE not found, skipping..."
                continue
            fi

            echo "Compiling $DIR/$FILE..."
            python3 -m py_compile "$DIR/$FILE"

            PYCACHE_DIR="$DIR/__pycache__"
            PYC_FILE=$(find "$PYCACHE_DIR" -name "$(basename "$FILE" .py)*.pyc" | head -n 1)
            if [ -z "$PYC_FILE" ]; then
                echo "Error: Could not find compiled .pyc file for $FILE in $DIR"
                exit 1
            fi

            DEST_PYC="$DIR/$(basename "$PYC_FILE")"
            mv "$PYC_FILE" "$DEST_PYC"
            echo "Moved $PYC_FILE to $DEST_PYC"

            rm "$DIR/$FILE"
            echo "Removed $DIR/$FILE"
        done
    done
}

# Clean up __pycache__ across all directories
clean_pycache() {
    for DIR in "${!SOURCE_DIRS[@]}"; do
        PYCACHE_DIR="$DIR/__pycache__"
        if [ -d "$PYCACHE_DIR" ]; then
            rm -rf "$PYCACHE_DIR"
            echo "Cleaned up $PYCACHE_DIR"
        fi
    done
}

# Update setup.py to include .pyc files from all directories
update_setup() {
    echo "Updating setup.py..."
    
    # Build package_data dynamically
    PACKAGE_DATA=""
    for DIR in "${!SOURCE_DIRS[@]}"; do
        # Convert directory path to package notation (replace / with .)
        PACKAGE_PATH="${DIR//\//.}"
        PACKAGE_DATA+="        '$PACKAGE_PATH': ['*.pyc'],"
    done
    # Remove trailing comma from the last entry
    PACKAGE_DATA="${PACKAGE_DATA%,}"

    cat > setup.py <<EOF
from setuptools import setup, find_packages

setup(
    name='$PACKAGE_NAME',
    version='$VERSION',
    description='A Python client for MontyCat, NoSQL store utilizing Data Mesh architecture.',
    packages=find_packages(),
    zip_safe=False,
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='MontyGovernance',
    author_email='eugene.and.monty@gmail.com',
    package_data={
$PACKAGE_DATA
    },
    install_requires=['orjson', 'xxhash', 'asyncio'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
EOF
    echo "Updated setup.py to include .pyc files from all directories"
}

# Build and push to PyPI
build_and_push() {
    echo "Building source distribution..."
    python3 setup.py sdist

    DIST_DIR="dist"
    TAR_FILE=$(find "$DIST_DIR" -name "$PACKAGE_NAME-$VERSION.tar.gz" | head -n 1)
    if [ -z "$TAR_FILE" ]; then
        echo "Error: Could not find the built .tar.gz file"
        exit 1
    fi

    if [ "$CI_DEPLOY" == "true" ] && [ -n "$PYPI_TOKEN" ]; then
        echo "Uploading $TAR_FILE to PyPI..."
        twine upload --repository pypi --username "__token__" --password "$PYPI_TOKEN" "$TAR_FILE"
        echo "Uploaded $TAR_FILE to PyPI"
    else
        echo "Dry run or PYPI_TOKEN not set. Skipping upload. Built file: $TAR_FILE"
    fi
}

# Main execution
main() {
    CI_DEPLOY="${CI_DEPLOY:-false}"  # Default to false unless set by CI
    check_prerequisites
    compile_file
    clean_pycache
    update_setup
    build_and_push
}

# Run the script
main