# config.nu
#
# Installed by:
# version = "0.105.1"
#
# This file is used to override default Nushell settings, define
# (or import) custom commands, or run any other startup tasks.
# See https://www.nushell.sh/book/configuration.html
#
# This file is loaded after env.nu and before login.nu
#
# You can open this file in your default editor using:
# config nu
#
# See `help config nu` for more options
#
# You can remove these comments if you want or leave
# them for future reference.
#
let home = $env.HOME
$env.XDG_CONFIG_HOME = $"($home)/.config"
$env.GOPATH = $"($home)/go"
$env.CLAUDE_CODE_USE_BEDROCK = "1"

let local_paths = [
  $"($home)/.local/bin"
  $"($home)/go/bin"
  $"($home)/.cargo/bin"
  $"($home)/.antigravity/antigravity/bin"
]
$env.PATH = ($env.PATH | append $local_paths | uniq)

if ("/opt/homebrew/bin" | path exists) {
  $env.PATH = ($env.PATH | prepend "/opt/homebrew/bin" | prepend "/opt/homebrew/sbin" | uniq)
} else if ("/home/linuxbrew/.linuxbrew/bin" | path exists) {
  $env.PATH = ($env.PATH | prepend "/home/linuxbrew/.linuxbrew/bin" | prepend "/home/linuxbrew/.linuxbrew/sbin" | uniq)
}

$env.EDITOR = (if (which nvim | is-empty) { "vim" } else { "nvim" })
$env.config.edit_mode = 'vi'
