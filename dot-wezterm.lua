local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.font = wezterm.font 'Fira Code'
config.default_prog = { "/opt/homebrew/bin/tmux" }

return config
