#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
IMAGE="$BUILD/richmackos-base-arm64.qcow2"
SIZE="${RICHMACK_DISK_SIZE:-16G}"
command -v qemu-img >/dev/null || { echo "qemu-img is required" >&2; exit 1; }
mkdir -p "$BUILD"
if [ -e "$IMAGE" ]; then
  echo "Base image already exists: $IMAGE"
  exit 0
fi
echo "Creating $SIZE ARM64 qcow2 base image..."
qemu-img create -f qcow2 "$IMAGE" "$SIZE"
qemu-img info "$IMAGE"
