#!/bin/bash

# This is installation script for github codespaces

set -euo pipefail

function install_brew() {
  sudo apt-get install build-essential
  if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # shellcheck disable=SC2016
    echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
  else
    echo "Homebrew is already installed."
  fi
}

install_brew

brew install stow

make install
