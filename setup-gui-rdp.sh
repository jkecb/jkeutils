#!/usr/bin/env bash
set -e

# === 1. System update ===
apt update && apt upgrade -y

# === 2. Create a new user with a generated password ===
USERNAME="vpsuser"
PASSWORD=$(openssl rand -base64 12)
adduser --disabled-password --gecos "" $USERNAME
echo "${USERNAME}:${PASSWORD}" | chpasswd
usermod -aG sudo $USERNAME

# === 3. Install Xfce GUI ===
apt install -y xfce4 xfce4-goodies

# === 4. Install and configure xRDP ===
apt install -y xrdp
systemctl enable xrdp
systemctl start xrdp

# Allow RDP through firewall (if ufw is enabled)
if command -v ufw >/dev/null 2>&1; then
    ufw allow 3389
fi

# === 5. Install Firefox ESR ===
apt install -y firefox-esr

# === 6. Print credentials ===
echo
echo "==========================================="
echo "✅ GUI + RDP setup complete on Debian 12"
echo "➡️  Connect using Microsoft Remote Desktop:"
echo "   Server: $(hostname -I | awk '{print $1}')"
echo "   Username: $USERNAME"
echo "   Password: $PASSWORD"
echo "==========================================="
echo "⚠️ Save this info now. The password won't be shown again."
