#!/usr/bin/env bash

# Installation script for GitHub Codespaces / Devcontainers
# Ensures dotfiles, Homebrew, pi coding agent, and neovim with all dependencies are installed.

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

echo "=== [1/6] Installing system dependencies from package list ==="
if command -v bindep &>/dev/null && [ -f "$SCRIPT_DIR/bindep.txt" ]; then
  echo "Using bindep to determine missing packages..."
  PACKAGES=$(bindep -b -f "$SCRIPT_DIR/bindep.txt" 2>/dev/null || true)
  if [ -n "$PACKAGES" ]; then
    if command -v apt-get &>/dev/null; then
      export DEBIAN_FRONTEND=noninteractive
      run_sudo apt-get update -y
      run_sudo apt-get install -y --no-install-recommends $PACKAGES
    elif command -v dnf &>/dev/null; then
      run_sudo dnf install -y $PACKAGES || true
    fi
  fi
elif command -v apt-get &>/dev/null && [ -f "$SCRIPT_DIR/packages/ubuntu.txt" ]; then
  export DEBIAN_FRONTEND=noninteractive
  run_sudo apt-get update -y
  PACKAGES=$(grep -v -E '^\s*#|^\s*$' "$SCRIPT_DIR/packages/ubuntu.txt" | tr '\n' ' ')
  run_sudo apt-get install -y --no-install-recommends $PACKAGES
elif command -v dnf &>/dev/null && [ -f "$SCRIPT_DIR/packages/fedora.txt" ]; then
  PACKAGES=$(grep -v -E '^\s*#|^\s*$' "$SCRIPT_DIR/packages/fedora.txt" | tr '\n' ' ')
  run_sudo dnf install -y $PACKAGES || true
fi

# Ensure fd is available in PATH (Debian/Ubuntu names binary fdfind)
if command -v fdfind &>/dev/null && ! command -v fd &>/dev/null; then
  run_sudo ln -sf "$(command -v fdfind)" /usr/local/bin/fd
fi

echo "=== [2/6] Installing Homebrew and pi coding agent ==="
if ! command -v brew &>/dev/null; then
  if [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
  elif [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    echo "Homebrew not found. Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
      eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    fi
  fi
fi

if [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
  eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
elif [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "Installing pi coding agent via Homebrew..."
brew install pi-coding-agent

echo "=== [3/6] Installing Codespaces packages via Homebrew bundle ==="
if [ -f "$SCRIPT_DIR/dot-Brewfiles/codespaces.Brewfile" ]; then
  brew bundle --file="$SCRIPT_DIR/dot-Brewfiles/codespaces.Brewfile" || true
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

echo "Neovim version: $(nvim --version 2>/dev/null | head -n 1 || echo 'unknown')"

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
echo "nvim version:     $(nvim --version 2>/dev/null | head -n 1 || echo 'unknown')"
echo "ripgrep location: $(command -v rg || echo 'not found')"
echo "fd location:      $(command -v fd || echo 'not found')"
echo "stow location:    $(command -v stow || echo 'not found')"
echo "brew location:    $(command -v brew || echo 'not found')"

echo "=== Dotfiles and dependencies installation complete! ==="
