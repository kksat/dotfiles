#!/bin/bash
set -euo pipefail

sudo apt-get install build-essential

NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

echo >> ~/.bashrc

# shellcheck disable=SC2016
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc  

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

brew install stow

make install
