#!/bin/bash
set -euo pipefail

VERSION="${1:-0.6.0}"
ARCH="arm64"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/vm/richmackos-test.qcow2"
DIST="$ROOT/dist"

OUTPUT="$DIST/richmackos-${VERSION}-${ARCH}.qcow2"
COMPRESSED="${OUTPUT}.xz"

echo "======================================"
echo "      RichmackOS Release Builder"
echo "======================================"
echo
echo "Version: $VERSION"
echo "Arch:    $ARCH"
echo

if [ ! -f "$SOURCE" ]; then
    echo "ERROR: $SOURCE not found"
    exit 1
fi

mkdir -p "$DIST"

echo "[1/4] Checking source image..."
qemu-img check "$SOURCE"

echo "[2/4] Creating clean release image..."
rm -f "$OUTPUT" "$COMPRESSED"

qemu-img convert \
    -p \
    -f qcow2 \
    -O qcow2 \
    -c \
    "$SOURCE" \
    "$OUTPUT"

echo "[3/4] Verifying release image..."
qemu-img check "$OUTPUT"

echo "[4/4] Compressing..."
xz -T0 -6 -v -k "$OUTPUT"

echo
echo "======================================"
echo "      RichmackOS BUILD COMPLETE"
echo "======================================"
echo

ls -lh "$OUTPUT" "$COMPRESSED"

echo
echo "SHA256:"
shasum -a 256 "$COMPRESSED"
