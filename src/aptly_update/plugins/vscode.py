"""
vscode.py

This is a plugin for aptly-update.py. It downloads Visual Studio Code and creates
a snapshot that can be used to publish it or merged with other snapshots.

Its tests are in the parent directory, along with aptly-update.py itself.
One test will fail without internet access. Parameters are passed in from
aptly-update.py, which reads them from a yaml file. See the aptly_update.py
documentation for more information about plugins.
"""

import requests
import re
from os.path import exists
import subprocess

def check_status(req: requests.models.Response):
    if req.status_code == 200:
        return True
    else:
        return False

def redirect_header(req: requests.models.Response):
    return re.findall("filename=(.+);", req.headers['Content-Disposition'])[0]

def qualify_filename(path, filename):
    if path[-1] != '/':
        path = path + '/'
    return path + filename

def check_file(filename):
    if exists(filename):
        return True
    else:
        return False

def get_file(url, fqfile, timeout, debug):
    cmd = "curl --no-progress-meter --max-time " + str(timeout) + " --write-out %{exitcode} --output " + fqfile + " '" + url + "' 2>&1"
    if debug:
        return cmd
    else:
        return subprocess.run(cmd, shell=True,
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.STDOUT,
                                    text=True).stdout

def fetch_repo(args):
    dbgprint(args['debug'], "Args:        ",  args)
    req = requests.head(args['url'], allow_redirects=True)
    if check_status(req):
        filename = redirect_header(req)
        dbgprint(args['debug'], "Filename:    ",  filename)
        fqfile = qualify_filename(args['path'], filename)
        rtn = ""
        if not check_file(fqfile):
            rtn = get_file(args['url'], fqfile, args['timeout'], args['debug'])
            dbgprint(args['debug'], "Curl:        ",  rtn)
        if check_file(fqfile) or args['debug']:
            cmd = "aptly repo add vscode " + fqfile + " >> " + args['logfile'] + " 2>&1" # type: ignore
            xqt(cmd, args['debug'])
            cmd = "aptly snapshot create vscode-" + args['timestamp'] + " from repo vscode >> " + args['logfile'] + " 2>&1" # type: ignore
            xqt(cmd, args['debug'])
        else:
            print("Error: Failed to download " + fqfile + " from " + args['url'])
            print('Result:' + rtn) # type: ignore
    else:
        print("Error: " + args['url'] + " is not a valid URL")

def dbgprint(dbg, text, obj):
    if dbg:
        print(text, obj)

def xqt(cmd, debug):
    if debug:
        print(cmd)
    else:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT,
                                          text=True).stdout
