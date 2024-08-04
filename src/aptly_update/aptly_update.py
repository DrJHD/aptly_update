"""
aptly_update.py

This script is used to update Aptly mirrors.

Usage:

    aptly_update.py -y <yaml file>
where <yaml file> is the name of the YAML file containing the configuration.
The -d flag can be used for debug mode. No updates will take place, but the
commands that would be sent to Aptly and the internet will be printed to the
screen.

Log files:

A log file are created automatically every time the script is run. The name will
be the name of the script followed by '-run-" and a date and time stamp. The
time stamp will be the time at which execution started and will be used for all
files and Aptly artefacts created during the run, but not for downloads. There
is, by design, no option to do without it.

The log files will be written to the same directory as the executable.

YAML file format examples:

- 
  name: bookworm
  mirrors:
    - bookworm-main

This is the simplest example, where a single existing mirror is updated and published,
albeit under a different name.

- 
  name: bookworm
  mirrors:
    - bookworm-main
    - bookworm-security

In this example, two existing mirrors are updated and published, again under a
single name.

- 
  name: bookworm
  mirrors:
    - bookworm-main
- 
  name: raspbian
  mirrors:
    - raspbian-main

This example publishes two mirrors. Each contains a single existing mirror.

- 
  name: bookworm
  mirrors:
    - bookworm-main
  plugins:
    - vscode:
        url: https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64
        path: /media/thumb/aptly/vscode
        timeout: 600

This example publishes a mirror with a plugin. The plugin must exist in a
subdirectory named "plugins". The name of the plugin is the same as the name of the
snapshot that will be generated locally. The parameters will vary with each application
and even with such things as the user's connection speed. I can download vscode in
about 4 minutes, so the 600 seconds timeout should be plenty. You may be faster
or slower. The path is where the download will be stored; again, this will be
dependent on your implementation.

Plugins:

It is impossible to define what information a plugin will need or the commands that
will run. The purpose of a plugin is to allow the admin to specify additional
packages and to publish them as additional repos or in combination with existing
mirrors. Plugins are stored in a subdirectory named "plugins". Their tests are
in the parent directory.

The name of the plugin is also the name of the snapshot that will be used. The yaml
must contain all the information the plugin needs, in a format that will result in
a dictionary containing the correct data structure. Three key/value pairs will be
added, 'timestamp', 'logfile' and 'debug'. This dictionary will be the only
parameter passed to the plugin. The plugin must contain a function called 'fetch_repo'
that will accept the dictionary as its only parameter.

Aptly configuration:

The script does not need any special privileges to run. This script cannot configure
aptly nor change its configuration. All mirrors must be set up by the admin.
However, additional packages can be added simply by amending the yaml file to include
a plugin and creating the directory where the download will be stored.

Aptly snapshots:

The aptly documentation states that snapshots use no space. A new snapshot is created
for every mirror, for every plugin and for every repo that contains more than one
mirror and/or plugin. This can lead to the snapshot list being hard to read and
manual culling is advised.

"""

import subprocess
import argparse
import sys
import yaml
import datetime
import platform

TIMESTAMP = datetime.datetime.now().strftime("%Y%m%dT%H:%M:%S")
LOGFILE   = sys.argv[0] + "-run-" + TIMESTAMP
SEPARATOR = "\\" if platform.system() == "Windows" else "/" # Because I'm developing on Windows

def main():
# Parses command line arguments using parse_args().
# If no YAML file is specified, it prints an error message and exits.
# If a YAML file is specified, it opens the file, loads its contents into a
# dictionary 'args'  and then iterates over it.
# For each top-level key, it updates and publishes a Debian mirror using Aptly.
#   Within each such key, it adds to the repo all named mirrors provided by 
#   other mirrors and adds any applications for which a plugin is specified.
    args = parse_args()
    if args.yaml is None:
            print("No YAML file specified. Dying.")
            sys.exit(1)
    else:
        with open(args.yaml[0]) as yaml_file:
            config = yaml.safe_load(yaml_file)
            dbgprint(args.debug, "Config:      ", config)
            for hash in config:
                publish = hash['name']
                dbgprint(args.debug, "Publish:     ", publish)
                count = 0
                list = ""
                snapshot = ""
                for mirror in hash['mirrors']:
                    snapshot = mirror
                    count += 1
                    list = list + mirror + "-" + get_timestamp() + " "
                    dbgprint(args.debug, "Mirror:      ", mirror)
                    xqt("aptly mirror update " + mirror + " >> " + get_logfile() + " 2>&1",
                         args.debug)
                    xqt("aptly snapshot create " + mirror + "-" + get_timestamp() + 
                        " from mirror " + mirror +  " >> " + get_logfile() + " 2>&1", args.debug)
                if 'plugins' in hash:
                    sys.path.append(sys.path[0] + SEPARATOR + 'plugins')
                    for plugin in hash['plugins']:
                        count += 1
                        plugin_name, plugin_dict = next(iter(plugin.items()))
                        list = list + plugin_name + "-" + get_timestamp() + " "
                        dbgprint(args.debug, "Plugin:      ", plugin_name)
                        mod = import_module(plugin_name, args.debug)
                        call_plugin(mod, plugin_dict, args.debug)
                if 1 < count:
                    xqt("aptly snapshot merge -latest " + publish + "-" + get_timestamp() + " " 
                        + list + ">> " + get_logfile() + " 2>&1", args.debug)
                    snapshot = publish
                xqt("aptly publish drop " + publish + " >> " + get_logfile() + " 2>&1", args.debug)
                xqt("aptly publish snapshot -distribution=" + publish + " " + snapshot + "-" + get_timestamp() + " >> " + get_logfile() + " 2>&1", args.debug)

def call_plugin(mod, plugin_dict, debug):
# Calls a plugin with the given module, plugin name, plugin dictionary, and debug mode.
#
# Args:
#     mod (module): The module containing the plugin.
#     plugin_name (str): The name of the plugin to call.
#     plugin_dict (dict): The dictionary containing the plugin's configuration.
#     debug (bool): Whether to enable debug mode.
#
# Returns:
#     None
#
# Raises:
#     None
#
# Side Effects:
#     - Calls the 'fetch_repo' method of the plugin module with the plugin dictionary.
    plugin_dict['timestamp'] = get_timestamp()
    plugin_dict['logfile'] = get_logfile()
    plugin_dict['debug'] = debug
    dbgprint(debug, "Dict:        ", plugin_dict)
    mod.fetch_repo(plugin_dict)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', 
                        help='debug mode', 
                        action='store_true')
    parser.add_argument('-y', '--yaml', '-f', '--file',
                        nargs=1,
                        help='YAML file name')
    args = parser.parse_args()
    if args.debug:
        print("Debug mode")
        print("Command line:", sys.argv)
        print("Arguments:   ", args)
        print("Timestamp:   ", get_timestamp())
        print("Logfile:     ", get_logfile())
    return args

def xqt(cmd, debug):
    if debug:
        print(cmd)
    else:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT,
                                          text=True).stdout

def get_timestamp():
    return TIMESTAMP

def get_logfile():
    return LOGFILE

def dbgprint(dbg, text, obj):
    if dbg:
        print(text, obj)

def import_module(name, debug):
    dbgprint(debug, "Plugin name: ", name)
    dbgprint(debug, "Module path: ", sys.path)
    return __import__(name)

if __name__ == '__main__':
    main()
