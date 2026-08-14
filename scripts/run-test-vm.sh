#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISK="$ROOT/vm/richmackos-test.qcow2"
EFI="$(brew --prefix qemu)/share/qemu/edk2-aarch64-code.fd"

echo "Starting RichmackOS ARM64..."
echo "Disk: $DISK"
echo "SSH:  ssh -p 2223 wisdom@localhost"
echo

qemu-system-aarch64 \
  -M virt,highmem=on \
  -accel hvf \
  -cpu host \
  -smp 4 \
  -m 4G \
  -device virtio-gpu-pci \
  -display cocoa,zoom-to-fit=on \
  -device qemu-xhci \
  -device usb-kbd \
  -device usb-tablet \
  -drive if=pflash,format=raw,readonly=on,file="$EFI" \
  -drive file="$DISK",if=virtio,format=qcow2 \
  -device virtio-net-pci,netdev=net0 \
  -netdev user,id=net0,hostfwd=tcp::2223-:22
