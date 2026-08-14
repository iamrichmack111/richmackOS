#!/bin/bash
set -euo pipefail

RICH_USER="${SUDO_USER:-wisdom}"
RICH_HOME="$(getent passwd "$RICH_USER" | cut -d: -f6)"

echo "======================================"
echo "       RichmackOS Bootstrap"
echo "======================================"

if [ "$EUID" -ne 0 ]; then
    echo "Run this script with sudo."
    exit 1
fi

echo "[1/10] Updating Debian..."
apt update

echo "[2/10] Installing RichmackOS base packages..."
grep -vE '^[[:space:]]*(#|$)' config/packages.txt | xargs apt install -y

echo "[3/10] Creating RichmackOS filesystem..."
mkdir -p \
    /opt/richmack/bin \
    /opt/richmack/apps \
    /opt/richmack/workspace \
    /opt/richmack/config \
    /opt/richmack/assets \
    /var/lib/richmack

echo "[4/10] Installing RichmackOS identity..."
cat > /etc/richmack-release <<'RELEASE'
NAME="RichmackOS"
VERSION="0.6.0"
ID=richmackos
ID_LIKE=debian
PRETTY_NAME="RichmackOS 0.6.0 (Debian 13)"
ARCHITECTURE="ARM64"
BUILD="Development"
RELEASE

echo "[5/10] Installing RichmackOS artwork..."
install -m 0644 assets/logo.ans /opt/richmack/assets/logo.ans

echo "[6/10] Installing RichmackOS commands..."
install -m 0755 scripts/rootfs/usr/local/bin/richmack-os \
    /usr/local/bin/richmack-os

install -m 0755 scripts/rootfs/usr/local/bin/richmack-info \
    /usr/local/bin/richmack-info

install -m 0755 scripts/rootfs/usr/local/bin/richmack-console \
    /usr/local/bin/richmack-console

echo "[7/10] Installing login branding..."
install -m 0755 scripts/rootfs/etc/profile.d/richmack-banner.sh \
    /etc/profile.d/richmack-banner.sh

echo "[8/10] Installing Richmack Workspace..."

if ! command -v pipx >/dev/null 2>&1; then
    apt install -y pipx
fi

sudo -u "$RICH_USER" \
    env HOME="$RICH_HOME" \
    pipx install richmack-workspace || \
sudo -u "$RICH_USER" \
    env HOME="$RICH_HOME" \
    pipx upgrade richmack-workspace

sudo -u "$RICH_USER" \
    env HOME="$RICH_HOME" \
    pipx ensurepath || true


echo "[9/10] Configuring RichmackOS console..."

mkdir -p /etc/systemd/system/getty@tty1.service.d

install -m 0644 \
    scripts/rootfs/etc/systemd/system/getty@tty1.service.d/override.conf \
    /etc/systemd/system/getty@tty1.service.d/override.conf

install -m 0644 \
    scripts/rootfs/home/wisdom/.bash_profile \
    "$RICH_HOME/.bash_profile"

chown "$RICH_USER:$RICH_USER" "$RICH_HOME/.bash_profile"

systemctl daemon-reload

echo "[10/10] Setting permissions..."
chown -R "$RICH_USER:$RICH_USER" \
    /opt/richmack/apps \
    /opt/richmack/workspace

echo
echo "======================================"
figlet "RICHMACK OS"
echo "Bootstrap complete."
echo "======================================"
echo
echo "User:      $RICH_USER"
echo "Workspace: $RICH_HOME/.local/bin/richmack-workspace"
echo
