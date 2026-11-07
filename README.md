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

1. Enable the supervised SSH tunnel on your Mac:

   ```sh
   ~/.local/bin/rex-pi-tunnel start
   ```

   The command enables the `com.ksatarin.rex-pi-ssh` LaunchAgent. It starts at
   sign-in and restarts SSH after connection loss, including after sleep or a
   network change. Running `start` again doesn't create a second tunnel.
   The tunnel uses `~/.ssh/rex-pi.sock` and bypasses pi's interactive tmux command
   without changing `ssh pi`.

   SSH authentication must work without a password or passphrase prompt. If SSH
   fails, the agent keeps retrying; enabling it doesn't guarantee a connection.

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

`status` checks the SSH connection process and returns a nonzero status if the
agent is stopped or SSH is reconnecting. `stop` disables both automatic retries
and startup at sign-in; run `start` to enable them again. Stopping the tunnel
doesn't stop the remote Rex server or its sessions.

SSH probes an idle connection every 15 seconds and exits after three unanswered
probes. After wake, detecting a broken connection can take about 45 seconds.
`launchd` retries failed workers with a 10-second throttle; reconnection also
depends on network availability and SSH authentication.

To inspect connection errors, read the log:

```sh
tail -n 50 ~/Library/Logs/rex-pi-ssh.log
```

The LaunchAgent runs `rex-pi-tunnel run` internally. Don't run that foreground
worker alongside the managed tunnel.
