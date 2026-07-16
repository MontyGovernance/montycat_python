#!/bin/bash

# Configuration
PACKAGE_NAME="montycat"
# setup.py is the SINGLE SOURCE OF TRUTH for all metadata (description,
# keywords, classifiers, project_urls). Derive the version from it — never
# regenerate the file, or a build would silently downgrade the PyPI SEO.
VERSION="$(grep -oE "version='[^']+'" setup.py | head -1 | cut -d\' -f2)"
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
    echo "Building $PACKAGE_NAME v$VERSION (metadata from setup.py)"
    check_prerequisites
    build_and_push
}

# Run the script
main