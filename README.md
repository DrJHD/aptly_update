# aptly_update.py

## Why

There are packages that are available as .deb files, but not from the official
Debian servers. Frequently, the distributors advise users to change their
apt sources list to include the distributor. Apt
has no tool to restrict certain distributors to certain packages. This means
that packages normally updated from official servers might instead come from
the distributor of such a package. This increases the attack surface.

On a site with multiple Debian machines, running a local mirror acts as a
cache, meaning that security updates use less bandwidth.
[Aptly](https://www.aptly.info/) is one of the tools that can serve a local
mirror.

This script performs two functions. First, it automates the updating of the
official repositories. Second, it enables unofficial packages to be
added without changing the sources and to be updated automatically.
Each additional package requires its own plugin.

## Prerequisites

* A server running Debian.
* A running, fully configured installation of [Aptly](https://www.aptly.info/doc/configuration/).
* Access to the user account under which Aptly runs.

## How

On an installation where "aptly" is a dedicated user with low rights, this script
can be installed in the home directory of the aptly user together with the yaml file
containing the configuration. There is a `plugins` subdirectory. `crontab -e`
was run as the aptly user and the line below added:

```
25 23   *   *   *    /usr/bin/python3 /home/aptly/aptly-update.py -y /home/aptly/aptly-update.yaml
```

This runs the script as the aptly user at 23:25 every day. The intention is that
it should finish running before the Debian machines start their unattended
security updates.

If the script is installed with `git clone`, it will be put into a
subdirectory and the crontab line above will have to change accordingly,
unless the file is moved.

## Python and me

I haven't written much Python, although I have been programming for fun since 1974.
I have never released anything in Python before, and this has been my first look
at the publication standards. I expect I have made lots of mistakes. I'm pretty
thick skinned and won't take offence at being told "it's bad because...", especially
if the "because" includes things I can read.

## Copyright

Copyright 2024 John Davies.

## Licence

This is licenced under the [Apache 2.0 licence](https://directory.fsf.org/wiki/License:Apache-2.0)

## Patches

Patches and additional plugins will be received gratefully
if they come with tests and documentation.
