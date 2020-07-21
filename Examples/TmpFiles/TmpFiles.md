# Temporary Files

## Description

The sequence of commands creates and executes a file using the `systemd-tmpfiles` directives in a `.conf` file:

* The `F` type will create a file if it does not exist yet, including any directories in its path that do not exist.
  In our case, `/tmp/.a/hello.sh` is created with permissions 0700 and uid/gid for the path are set to 1000.
  By default, the directory, `/tmp/.a` is created with 0755 permissions.
* The `w` type writes the argument parameter to a file, if the file exists. Takes specifiers such as `%u` for the running username.
  In our case, `/bin/echo "hello $USER"` is written to the file `/tmp/.a/hello.sh`
* The `R` type recursively removes a path and all its subdirectories (if it is a directory).
  In our case, the `/tmp/.a` directory and all its contents are removed.

**Source:** Type descriptions copied from: <https://www.freedesktop.org/software/systemd/man/tmpfiles.d.html>

**Note:** Specifiers table can be found in: <https://www.freedesktop.org/software/systemd/man/tmpfiles.d.html#Specifiers>

## Additional Notes

* `systemd-tmpfiles` is a system for handling temporary files (creating, deleting, truncating files, named pipes, etc.)
  * While intended for temporary file locations (such as `/tmp/`, `/run/`), nothing prevents writing to non-temporary directories
    so long as the running user has appropriate permissions to it (such as the user's `/home/` directory)
* This command is automatically scheduled by systemd under certain scenarios
* See [tmpfiles.d](https://www.freedesktop.org/software/systemd/man/tmpfiles.d.html) for more information on types
* FIFO files, like the one used in [ScheduledRevShell.md](../ScheduledReverseShell/ScheduledRevShell.md) can be created with the `p` type
* The "Age" field in each directive specifies how old the file must be (in seconds) before it is cleaned up automatically by the system.
  Setting this field to 0 tells systemd to clean the file/folder every time its cleanup task runs.

## Step by Step

1. Generate a tmpfiles `.conf` file

```ini
$ cat exec-file.conf
#Type   Path                Mode    User    Group   Age     Argument
F       /tmp/.a/hello.sh    0700    1000    1000    0       -
w       /tmp/.a/hello.sh    -       -       -       -       /bin/echo "hello %u"
R       /tmp/.a             -       -       -       -       -
```

2. Install into the systemd user folder

```sh
$ mkdir -p ~/.config/user-tmpfiles.d/
$ ln -s `pwd`/exec-file.conf ~/.config/user-tmpfiles.d/
$
```

3. Execute the `--create` directives of the `.conf` file

```sh
$ ls /tmp/.a/
ls: cannot access '/tmp/.a/': No such file or directory
$ systemd-tmpfiles --user --create
$ ls -al /tmp/.a/
total 12
drwx------   2 user user     4096 Jan 23 10:33 .
drwxrwxrwt 119 root   root   4096 Jan 23 10:33 ..
-rwx------   1 user user       23 Jan 23 10:33 hello.sh
```

4. Manually execute the created file

```sh
$ /tmp/.a/hello.sh
hello ch0mler
```

5. Execute the `--remove` directives of the `.conf` file

```sh
$ systemd-tmpfiles --user --remove
$ ls -al /tmp/.a/
ls: cannot access '/tmp/.a': No such file or directory
```

### Ambiguous Flags

Much like PowerShell, systemd can attempt to resolve flags that don't quite match exactly.
However, unlike PowerShell, flags are still case-sensitive. Mixed-case or all-caps raise errors.

For example:

  ```sh
  $ systemd-tmpfiles --user --c
  systemd-tmpfiles: option '--c' is ambiguous; possibilities: '--cat-config' '--create' '--clean'
  $ systemd-tmpfiles --user --cr
  $ ls -al /tmp/.a/
    total 12
    drwx------   2 user user     4096 Jan 23 10:33 .
    drwxrwxrwt 119 root   root   4096 Jan 23 10:33 ..
    -rwx------   1 user user       23 Jan 23 10:33 hello.sh
  ```

  ```sh
  $ systemd-tmpfiles --user --r
  systemd-tmpfiles: option '--r' is ambiguous; possibilities: '--remove' '--root' '--replace'
  $ systemd-tmpfiles --user --rem
  $ ls /tmp/.a
  ls: cannot access '/tmp/.a': No such file or directory
  ```

### Alternative Invocations

There are a couple alternative methods for invoking directives within a configuration.

1. On the command-line by referencing an absolute path

  ```sh
  $ systemd-tmpfiles --remove `pwd`/exec-file.conf
  $ ls /tmp/.a/
  ls: cannot access '/tmp/.a/': No such file or directory
  ```

2. By passing directives through STDIN

  ```sh
  $ cat exec-file.conf | systemd-tmpfiles --remove -
  $ ls /tmp/.a/
  ls: cannot access '/tmp/.a/': No such file or directory
  ```
