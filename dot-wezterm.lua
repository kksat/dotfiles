local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.font = wezterm.font 'Fira Code'

if wezterm.target_triple == "x86_64-apple-darwin" or wezterm.target_triple == "aarch64-apple-darwin" then
  config.default_prog = { "/opt/homebrew/bin/tmux" }
end

return config
