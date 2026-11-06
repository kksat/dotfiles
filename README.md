# dot
dot files

Use this repo

```bash
wget -O - bit.ly/dotbash | bash
```

Pre-commit

```bash
brew install pre-commit gitleaks
pre-commit install
```

## Connect Rex to pi over SSH

Use this setup to access pi's native Rex sessions through SSH rather than
Tailscale. It requires your existing `ssh pi` configuration and a personal Rex
server listening at `/run/user/1000/rex/server.sock` on pi.

After you stow the dotfiles:

1. Start the background SSH tunnel on your Mac:

   ```sh
   ~/.local/bin/rex-pi-tunnel start
   ```

   The command creates `~/.ssh/rex-pi.sock`. Running it again reuses the active
   tunnel. It bypasses pi's interactive tmux command without changing `ssh pi`.

2. Reload the Rex configuration on your Mac:

   ```sh
   rex config reload
   ```

   `~/.config/rex/init.lua` declares the host as `pi-ssh`. Select that host in
   Rex for Mac.

3. Verify that Rex reaches your remote sessions:

   ```sh
   rex -S pi-ssh ls
   ```

   The list contains the same sessions as the existing Tailscale connection.

To check or stop only this tunnel, run:

```sh
~/.local/bin/rex-pi-tunnel status
~/.local/bin/rex-pi-tunnel stop
```

The tunnel runs in the background, but doesn't restart automatically after a
reboot or connection loss. Run `start` again to reconnect. Stopping the tunnel
doesn't stop the remote Rex server or its sessions.
