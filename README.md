# 🧠 RichmackOS

> **A lightweight, terminal-first ARM64 Linux operating system built around the Richmack application ecosystem.**

![Platform](https://img.shields.io/badge/platform-ARM64-blue)
![Base](https://img.shields.io/badge/base-Debian%2013-red)
![Kernel](https://img.shields.io/badge/kernel-Linux%206.12-purple)
![Interface](https://img.shields.io/badge/interface-Terminal%20First-black)
![Virtualization](https://img.shields.io/badge/virtualization-QEMU-green)
![Version](https://img.shields.io/badge/version-0.4.0-cyan)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

---

## 🚀 What is RichmackOS?

**RichmackOS** is a lightweight ARM64 Linux operating system designed around a terminal-first workflow and the Richmack Python/TUI application ecosystem.

Rather than starting with a traditional desktop environment and removing components, RichmackOS begins with a minimal Debian ARM64 userspace and builds upward.

The current system includes:

- 🐧 Debian 13 ARM64 base
- ⚙️ Linux ARM64 kernel
- 🥾 UEFI / GRUB ARM64 boot
- 🖥️ Terminal-first system interface
- 🎨 ANSI boot/login branding
- 🔤 FIGlet interface branding
- 📦 Python + pipx application environment
- 🧰 Richmack Workspace
- 🔐 OpenSSH administration
- 🌐 NetworkManager
- 🛡️ sudo-based privilege management
- 👤 dedicated `wisdom` user
- 📟 automatic local-console startup
- 🧪 QEMU development environment
- 🏗️ debootstrap-based image construction

RichmackOS is intended to become a compact environment for launching and managing the growing family of Richmack terminal applications.

---

# ✨ Current Version

```text
RichmackOS 0.4.0
Architecture: ARM64 / AArch64
Base: Debian 13
Kernel: Linux 6.12
Boot: UEFI + GRUB ARM64
Default user: wisdom
Interface: Terminal / TUI
Virtualization: QEMU
```

Version `0.4.0` is the first RichmackOS image built directly from a Debian ARM64 root filesystem using `debootstrap`, rather than manually installing Debian through the graphical/text installer.

---

# 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      Apple Silicon   │
                    │         macOS        │
                    └──────────┬───────────┘
                               │
                               │ QEMU + HVF
                               ▼
                    ┌──────────────────────┐
                    │     UEFI Firmware    │
                    │      ARM64 EFI       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │         GRUB         │
                    │      ARM64 EFI       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Linux 6.12 ARM64  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Debian 13       │
                    │       Trixie         │
                    └──────────┬───────────┘
                               │
                               ▼
                 ┌─────────────────────────────┐
                 │         RichmackOS          │
                 │                             │
                 │  Branding                   │
                 │  Console                    │
                 │  Workspace                  │
                 │  Application Launcher       │
                 │  System Information         │
                 │  SSH Administration         │
                 └─────────────┬───────────────┘
                               │
                               ▼
                 ┌─────────────────────────────┐
                 │   Richmack TUI Ecosystem    │
                 │                             │
                 │   Python / pipx apps        │
                 │   Textual applications      │
                 │   local databases           │
                 │   CLI utilities             │
                 └─────────────────────────────┘
```

---

# 🖥️ Terminal-First Design

RichmackOS is intentionally designed around the terminal.

The local QEMU console automatically enters the RichmackOS user environment:

```text
UEFI
  ↓
GRUB
  ↓
Linux
  ↓
systemd
  ↓
tty1
  ↓
automatic wisdom login
  ↓
richmack-console
  ↓
richmack-os
```

SSH behaves differently:

```text
Mac Terminal
    ↓
SSH
    ↓
wisdom@richmack
    ↓
RichmackOS administrative shell
```

This creates two distinct interfaces:

### 🖥️ Local Console

Designed as the normal RichmackOS experience.

```text
RichmackOS
   │
   ├── Richmack Workspace
   ├── Applications
   ├── System Information
   ├── Updates
   ├── Terminal
   ├── Reboot
   └── Shutdown
```

### 🔧 SSH Administration

Provides a standard Linux shell for development, repair, upgrades, and system administration.

---

# 🎨 RichmackOS Branding

The operating system includes a custom ANSI logo and FIGlet title.

Assets are stored under:

```text
/opt/richmack/assets/
```

For example:

```text
/opt/richmack/assets/logo.ans
```

The terminal login environment uses:

```text
/etc/profile.d/richmack-banner.sh
```

The main RichmackOS commands include:

```text
/usr/local/bin/richmack-os
/usr/local/bin/richmack-info
/usr/local/bin/richmack-console
```

---

# 📦 Richmack Workspace

RichmackOS is built around the **Richmack Workspace**.

The Workspace acts as the centralized launcher and management environment for Richmack applications.

Installed with:

```bash
pipx install richmack-workspace
```

Launch with:

```bash
richmack-workspace
```

or through the RichmackOS menu:

```bash
richmack-os
```

The long-term goal is to allow RichmackOS to install, update, manage, and launch Richmack applications directly from the Workspace.

---

# 🧩 Richmack Application Ecosystem

RichmackOS is designed to host terminal applications from the broader Richmack ecosystem.

Examples include projects such as:

- 🧙 Wize Wizard
- 🧞 JinnLab
- 📖 Hebrew Fuzzy Study
- 🏋️ Exercise / fitness TUIs
- 🧮 calculation utilities
- 📝 journal applications
- 📚 study applications
- 🎵 RichPlayer
- 🔊 Piper Studio
- 🛡️ security / auditing tools
- 🔍 search and research utilities
- 💼 job-search TUIs
- 🗂️ CRM applications
- 📊 strategy and analysis tools

Applications are generally distributed independently through Python packaging and can be installed with `pipx`.

---

# 📂 Repository Structure

```text
richmackOS/
│
├── assets/
│   └── logo.ans
│
├── config/
│   ├── packages.txt
│   └── preseed/
│
├── scripts/
│   ├── bootstrap-richmackos.sh
│   ├── build-richmackos.sh
│   ├── build-release.sh
│   ├── create-base-image.sh
│   ├── run-test-vm.sh
│   │
│   └── rootfs/
│       ├── etc/
│       │   ├── profile.d/
│       │   │   └── richmack-banner.sh
│       │   │
│       │   └── systemd/
│       │       └── system/
│       │           └── getty@tty1.service.d/
│       │               └── override.conf
│       │
│       ├── home/
│       │   └── wisdom/
│       │       └── .bash_profile
│       │
│       └── usr/
│           └── local/
│               └── bin/
│                   ├── richmack-os
│                   ├── richmack-info
│                   └── richmack-console
│
├── build/
│   └── v0.4/
│       └── richmackos-0.4-arm64.qcow2
│
├── dist/
│   └── richmackos-0.3-arm64.qcow2.xz
│
├── iso/
│   └── debian-13.6.0-arm64-netinst.iso
│
└── vm/
    └── richmackos.qcow2
```

Generated VM images should generally **not** be committed directly to Git.

Use GitHub Releases for compressed operating-system images.

---

# 🔨 How RichmackOS Is Built

RichmackOS originally began as a manually customized Debian ARM64 virtual machine.

The build process later evolved into a direct image-construction workflow.

Current architecture:

```text
Blank QCOW2
    ↓
GPT partition table
    ↓
EFI partition
    +
ext4 root partition
    ↓
debootstrap Debian 13 ARM64
    ↓
install ARM64 kernel
    ↓
install GRUB ARM64 EFI
    ↓
install networking + SSH
    ↓
create wisdom user
    ↓
install Python / pipx
    ↓
apply RichmackOS bootstrap
    ↓
install Richmack branding
    ↓
install Workspace
    ↓
bootable RichmackOS QCOW2
```

This avoids requiring the Debian Installer for normal image generation.

---

# 🧱 Disk Layout

The current development image uses a **16 GiB virtual QCOW2 disk**.

```text
GPT
│
├── EFI System Partition
│      ~512 MB
│      FAT32
│      label: RICHMACKEFI
│
└── Root Partition
       remaining disk
       ext4
       label: RichmackOS
```

The ARM64 EFI fallback bootloader is installed at:

```text
/boot/efi/EFI/BOOT/BOOTAA64.EFI
```

This allows UEFI firmware such as QEMU's EDK2 firmware to discover the operating system without requiring a persistent NVRAM boot entry.

---

# 💻 Requirements

## Apple Silicon Mac

Recommended development platform:

```text
Apple Silicon Mac
macOS
Homebrew
QEMU
```

Install QEMU:

```bash
brew install qemu
```

Verify:

```bash
qemu-system-aarch64 --version
qemu-img --version
```

---

# 🚀 Running RichmackOS on macOS

Assuming a RichmackOS ARM64 QCOW2 image:

```text
richmackos-0.4-arm64.qcow2
```

start it with:

```bash
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
  -drive if=pflash,format=raw,readonly=on,file="$(brew --prefix qemu)/share/qemu/edk2-aarch64-code.fd" \
  -drive file=richmackos-0.4-arm64.qcow2,if=virtio,format=qcow2 \
  -device virtio-net-pci,netdev=net0 \
  -netdev user,id=net0,hostfwd=tcp::2224-:22
```

The VM should boot directly into the RichmackOS console.

---

# 🔐 SSH Access

The development QEMU configuration forwards host port `2224` to guest SSH port `22`.

Connect from macOS:

```bash
ssh -p 2224 wisdom@localhost
```

The SSH environment intentionally opens a normal administrative Bash shell instead of automatically opening the RichmackOS menu.

Launch the operating-system interface manually with:

```bash
richmack-os
```

---

# 👤 Default Development Account

Development builds currently use:

```text
Username: wisdom
```

Development images may temporarily use a build password while the image pipeline is evolving.

⚠️ **Change development passwords before distributing a public image.**

For production releases, RichmackOS should eventually implement a first-boot account setup rather than shipping a universal default password.

---

# 🧠 RichmackOS Commands

## Main OS interface

```bash
richmack-os
```

## System information

```bash
richmack-info
```

## Console launcher

```bash
richmack-console
```

## Workspace

```bash
richmack-workspace
```

---

# 🛠️ Administrative Commands

Check release information:

```bash
cat /etc/richmack-release
```

Check architecture:

```bash
uname -m
```

Expected:

```text
aarch64
```

Check kernel:

```bash
uname -r
```

Check services:

```bash
systemctl status ssh
systemctl status NetworkManager
```

Check network:

```bash
ip addr
```

Check storage:

```bash
lsblk
df -h
```

---

# 📜 RichmackOS Release Metadata

RichmackOS uses:

```text
/etc/richmack-release
```

Example:

```text
NAME="RichmackOS"
VERSION="0.4.0"
ID=richmackos
ID_LIKE=debian
PRETTY_NAME="RichmackOS 0.4.0 (Debian 13)"
ARCHITECTURE="ARM64"
BUILD="Development"
```

---

# 🏗️ Building the Debian Base

RichmackOS v0.4 uses `debootstrap`.

Example:

```bash
debootstrap \
  --arch=arm64 \
  trixie \
  /mnt/richmackos \
  http://deb.debian.org/debian
```

This creates a minimal Debian ARM64 userspace without launching the Debian Installer.

A typical initial base filesystem is only a few hundred megabytes before the kernel, system services, Python environment, and Richmack applications are installed.

---

# 🥾 ARM64 Bootloader

RichmackOS uses GRUB EFI for ARM64.

Example installation:

```bash
grub-install \
  --target=arm64-efi \
  --efi-directory=/boot/efi \
  --bootloader-id=RichmackOS \
  --removable \
  --no-nvram
```

Then:

```bash
update-grub
```

The important fallback loader is:

```text
EFI/BOOT/BOOTAA64.EFI
```

---

# 🐍 Python Application Environment

Python applications should generally **not** be installed globally with `pip`.

RichmackOS uses `pipx` to isolate application environments:

```bash
pipx install richmack-workspace
```

Useful commands:

```bash
pipx list
pipx install PACKAGE
pipx upgrade PACKAGE
pipx uninstall PACKAGE
```

---

# 📦 Creating a Release Image

QCOW2 images can be converted into a clean compressed QCOW2:

```bash
qemu-img convert \
  -p \
  -f qcow2 \
  -O qcow2 \
  -c \
  source.qcow2 \
  richmackos-0.4-arm64.qcow2
```

Validate:

```bash
qemu-img check richmackos-0.4-arm64.qcow2
```

Compress:

```bash
xz -T0 -6 -v -k richmackos-0.4-arm64.qcow2
```

Generate SHA-256:

```bash
shasum -a 256 richmackos-0.4-arm64.qcow2.xz
```

Release artifacts should resemble:

```text
richmackos-0.4-arm64.qcow2.xz
richmackos-0.4-arm64.qcow2.xz.sha256
```

---

# 📥 Installing From a Release

Download the compressed image from GitHub Releases.

Decompress:

```bash
xz -dk richmackos-0.4-arm64.qcow2.xz
```

Verify:

```bash
qemu-img check richmackos-0.4-arm64.qcow2
```

Then boot using the QEMU command shown above.

---

# 🍎 Apple Silicon Notes

RichmackOS currently targets:

```text
ARM64
AArch64
```

This makes Apple Silicon Macs an excellent development platform because QEMU can use Apple's Hypervisor Framework:

```text
-accel hvf
```

instead of fully emulating another CPU architecture.

This provides significantly better performance than emulating x86_64.

---

# 🧪 Development Workflow

The development model currently looks like:

```text
Mac
 │
 ├── source repository
 │
 ├── QEMU
 │
 └── build artifacts
       │
       ▼
RichmackOS builder VM
       │
       ├── qemu-nbd
       ├── debootstrap
       ├── parted
       ├── mkfs
       ├── chroot
       └── GRUB
              │
              ▼
      new RichmackOS image
              │
              ▼
             Mac
              │
              ▼
          QEMU testing
```

A major future goal is wrapping these steps into a single reproducible build command.

---

# 🗺️ Roadmap

## ✅ v0.1

- Debian ARM64 base
- QEMU boot
- SSH access
- Python environment

## ✅ v0.2

- ANSI Richmack branding
- FIGlet branding
- RichmackOS control interface
- tty1 automatic console startup
- Richmack Workspace integration

## ✅ v0.3

- Reproducible bootstrap
- Clean Debian reproduction test
- QCOW2 release artifact
- XZ compression
- SHA-256 release validation

## 🚧 v0.4

- debootstrap-based ARM64 image construction
- direct GPT/EFI filesystem creation
- ARM64 GRUB installation
- independent 16 GB image
- Debian Installer removed from image build path
- improved build automation

## 🔮 Future

- one-command image builder
- GitHub Actions image builds
- signed release checksums
- first-boot user creation
- application manifest
- Workspace-managed application installation
- update channels
- RichmackOS package repository
- x86_64 build
- Raspberry Pi / ARM hardware experiments
- USB / physical-device installation
- optional lightweight desktop profile
- Secure Boot research
- reproducible release manifests

---

# 🔒 Security Notes

RichmackOS is currently under active development.

Development images may include:

- automatic local console login
- temporary development passwords
- SSH enabled by default
- development-only configuration

These are convenient while building the OS but should not automatically be considered production-safe defaults.

Public releases should eventually implement:

```text
first boot
   ↓
create administrator
   ↓
set password
   ↓
configure SSH
   ↓
select RichmackOS profile
```

---

# 🧰 Troubleshooting

## QEMU image is locked

If you see:

```text
Failed to get shared "write" lock
```

another QEMU process probably has the image open.

Check:

```bash
ps aux | grep '[q]emu'
```

---

## SSH does not connect

Verify QEMU contains:

```text
hostfwd=tcp::2224-:22
```

Then:

```bash
ssh -p 2224 wisdom@localhost
```

---

## Check image integrity

```bash
qemu-img check IMAGE.qcow2
```

---

## Inspect image metadata

```bash
qemu-img info IMAGE.qcow2
```

---

## Richmack command not found

Check:

```bash
which richmack-os
which richmack-info
which richmack-workspace
```

For pipx applications:

```bash
pipx ensurepath
```

Then start a new shell.

---

# 🤝 Contributing

RichmackOS is currently an experimental personal operating-system project, but issues, ideas, testing, and technical feedback are welcome.

Areas especially useful for contribution include:

- ARM64 boot testing
- QEMU configuration
- Debian image engineering
- build automation
- reproducibility
- Textual/TUI design
- packaging
- security hardening
- hardware support
- CI/CD

---

# 🌐 Richmack Ecosystem

RichmackOS exists as part of the broader Richmack software ecosystem.

Website:

**https://richmack111.com**

GitHub:

**https://github.com/iamrichmack111**

Python applications are increasingly distributed through PyPI and managed through Richmack Workspace.

---

# 🧠 Philosophy

RichmackOS explores a simple idea:

> A modern personal computing environment does not need to begin with a desktop.

Instead:

```text
Linux
  +
terminal
  +
structured workflows
  +
small specialized applications
  +
automation
  =
a complete computing environment
```

RichmackOS treats the terminal as the primary workspace rather than a secondary administrative tool.

---

# ⚠️ Project Status

RichmackOS is currently an **experimental development operating system**.

It is suitable for:

- QEMU experimentation
- ARM64 development
- terminal application testing
- OS engineering practice
- Richmack application integration

It should **not yet be treated as a hardened production operating system**.

---

# 📄 License

Licensing information will be finalized as the project matures.

The Debian components retain their respective upstream licenses.

Third-party software installed through RichmackOS retains its original licensing.

---

<div align="center">

# 🧠 RICHMACK OS

### Terminal-First Linux

**Think. Build. Automate.**

Built on Debian ARM64.

Designed for the Richmack ecosystem.

</div>
