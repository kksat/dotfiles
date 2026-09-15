#!/usr/bin/env bash

# Installation script for GitHub Codespaces / Devcontainers
# Ensures dotfiles, pi (coding agent), and neovim with all dependencies are installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

run_sudo() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  elif command -v sudo &>/dev/null; then
    sudo "$@"
  else
    "$@"
  fi
}

echo "=== [1/6] Installing system dependencies ==="
if command -v apt-get &>/dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  run_sudo apt-get update -y
  run_sudo apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    unzip \
    tar \
    gzip \
    ripgrep \
    fd-find \
    python3 \
    python3-pip \
    python3-venv \
    stow
elif command -v dnf &>/dev/null; then
  run_sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    git \
    curl \
    tar \
    gzip \
    unzip \
    ripgrep \
    fd-find \
    python3 \
    python3-pip \
    stow || true
fi

# Ensure fd is available in PATH (Debian/Ubuntu names binary fdfind)
if command -v fdfind &>/dev/null && ! command -v fd &>/dev/null; then
  run_sudo ln -sf "$(command -v fdfind)" /usr/local/bin/fd
fi

echo "=== [2/6] Ensuring Node.js and npm are installed ==="
NEED_NODE=false
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
  NEED_NODE=true
else
  NODE_MAJOR="$(node -v | sed 's/v\([0-9]*\).*/\1/')"
  if [ "${NODE_MAJOR:-0}" -lt 18 ]; then
    NEED_NODE=true
  fi
fi

if [ "$NEED_NODE" = true ]; then
  echo "Installing Node.js LTS..."
  if command -v apt-get &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | run_sudo -E bash -
    run_sudo apt-get install -y nodejs
  fi
fi

echo "Node version: $(node -v)"
echo "NPM version:  $(npm -v)"

echo "=== [3/6] Installing pi coding agent and companions ==="
if ! command -v pi &>/dev/null; then
  echo "Installing @earendil-works/pi-coding-agent..."
  if [ "$(id -u)" -eq 0 ]; then
    npm install -g @earendil-works/pi-coding-agent
  else
    run_sudo npm install -g @earendil-works/pi-coding-agent
  fi
else
  echo "pi is already installed: $(pi --version 2>/dev/null || echo 'present')"
fi

# Install opencode CLI for opencode.nvim plugin
if ! command -v opencode &>/dev/null; then
  echo "Installing opencode-ai CLI..."
  if [ "$(id -u)" -eq 0 ]; then
    npm install -g opencode-ai || true
  else
    run_sudo npm install -g opencode-ai || true
  fi
fi

echo "=== [4/6] Ensuring modern Neovim (>= 0.10) is installed ==="
NEED_NVIM=false
if ! command -v nvim &>/dev/null; then
  NEED_NVIM=true
else
  NVIM_VER="$(nvim --version | head -n 1 | grep -oE '[0-9]+\.[0-9]+' | head -n 1 || true)"
  MAJOR="$(echo "$NVIM_VER" | cut -d. -f1)"
  MINOR="$(echo "$NVIM_VER" | cut -d. -f2)"
  if [ "${MAJOR:-0}" -eq 0 ] && [ "${MINOR:-0}" -lt 10 ]; then
    NEED_NVIM=true
  fi
fi

if [ "$NEED_NVIM" = true ]; then
  echo "Installing latest Neovim binary..."
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64)
      NVIM_ARCH="linux-x86_64"
      ;;
    aarch64|arm64)
      NVIM_ARCH="linux-arm64"
      ;;
    *)
      NVIM_ARCH="linux-x86_64"
      ;;
  esac

  TMP_NVIM="$(mktemp -d)"
  curl -fsSL "https://github.com/neovim/neovim/releases/latest/download/nvim-${NVIM_ARCH}.tar.gz" -o "$TMP_NVIM/nvim.tar.gz"
  run_sudo tar -C /usr/local --strip-components=1 -xzf "$TMP_NVIM/nvim.tar.gz"
  rm -rf "$TMP_NVIM"
fi

echo "Neovim version: $(nvim --version | head -n 1)"

echo "=== [5/6] Setting up dotfiles ==="
# Clone kksat/nvim configuration if missing
if [ ! -d "dot-config/nvim" ]; then
  echo "Cloning kksat/nvim..."
  mkdir -p dot-config
  git clone https://github.com/kksat/nvim.git dot-config/nvim
fi

# Update submodules if possible
git submodule update --init --recursive || true

# Remove default skeleton files from home so stow does not conflict or overwrite repo files
for f in .bashrc .zshrc .zprofile .profile .bash_profile .bash_login; do
  if [ -f "$HOME/$f" ] && [ ! -L "$HOME/$f" ]; then
    rm -f "$HOME/$f"
  fi
done

if command -v stow &>/dev/null; then
  echo "Stowing dotfiles to $HOME..."
  stow --dotfiles --restow . --target="$HOME"
fi

echo "=== [6/6] Syncing Neovim plugins ==="
nvim --headless "+Lazy! sync" +qa || true

echo "=== Verification ==="
echo "pi location:      $(command -v pi || echo 'not found')"
echo "pi version:       $(pi --version 2>/dev/null || echo 'unknown')"
echo "nvim location:    $(command -v nvim || echo 'not found')"
echo "nvim version:     $(nvim --version | head -n 1)"
echo "ripgrep location: $(command -v rg || echo 'not found')"
echo "fd location:      $(command -v fd || echo 'not found')"
echo "stow location:    $(command -v stow || echo 'not found')"

echo "=== Dotfiles and dependencies installation complete! ==="

