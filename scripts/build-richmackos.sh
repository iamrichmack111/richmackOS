#!/bin/bash
set -euo pipefail

VERSION="${1:-0.6.0}"
ARCH="arm64"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
DIST="$ROOT/dist"

echo "======================================"
echo "        RichmackOS Image Builder"
echo "======================================"
echo
echo "Version: $VERSION"
echo "Arch:    $ARCH"
echo

mkdir -p "$BUILD" "$DIST"

echo "[1/5] Checking QEMU..."

command -v qemu-system-aarch64 >/dev/null
command -v qemu-img >/dev/null

qemu-system-aarch64 --version | head -1

echo
echo "[2/5] Validating RichmackOS source..."

test -f "$ROOT/scripts/bootstrap-richmackos.sh"
test -f "$ROOT/scripts/create-base-image.sh"
test -f "$ROOT/config/packages.txt"
test -f "$ROOT/assets/logo.ans"

echo "PASS"

echo
echo "[3/5] Validating bootstrap..."

bash -n "$ROOT/scripts/bootstrap-richmackos.sh"

echo "PASS"

echo
echo "[4/5] Creating ARM64 base disk..."

"$ROOT/scripts/create-base-image.sh"

echo
echo "[5/5] Checking base disk..."

qemu-img check "$BUILD/richmackos-base-arm64.qcow2"

echo
echo "======================================"
echo "      RichmackOS v$VERSION"
echo "      BUILD STAGE 1 COMPLETE"
echo "======================================"
echo
echo "Base disk:"
echo "  $BUILD/richmackos-base-arm64.qcow2"
echo
echo "Next stage: unattended Debian installation."
