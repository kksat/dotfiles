-- Start the SSH forward with ~/.local/bin/rex-pi-tunnel.
rex.host({
	label = "pi-ssh",
	endpoint = os.getenv("HOME") .. "/.ssh/rex-pi.sock",
})
