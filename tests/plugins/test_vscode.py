import unittest
import plugins.vscode
from unittest.mock import Mock
from os.path import exists
import os
import subprocess
import re
from aptly_update import import_module
import sys
import platform
# import requests

SEPARATOR = "\\" if platform.system() == "Windows" else "/" # Because I'm developing on Windows

def get_parse_output(yaml):
    cmd = "python aptly_update.py -d --yaml test.yaml"
    with open("test.yaml", "w") as yaml_file:
        yaml_file.write(yaml)
    rtn = subprocess.run(cmd, stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                                text=True).stdout
    os.remove("test.yaml")
    # The yaml file must be removed before the assertions, as failure will
    # lead to a premature exit and an orphaned file.
    timematch = re.search(r'Timestamp:\s+(\d{8}T\d{2}:\d{2}:\d{2})', rtn)
    timestamp = timematch.group(1) # type: ignore
    logmatch = re.search(r'Logfile:\s+(.+\d{8}T\d{2}:\d{2}:\d{2})', rtn)
    logfile = logmatch.group(1) # type: ignore
    # The timestamp and logfile must be parsed rather than queried from the
    # code, as the two runs would be at different times.
    return (timestamp, logfile, rtn)

class TestGoodUrl(unittest.TestCase):
    def test_good_url(self):
        req = Mock()
        req.status_code = 200
        rtn = plugins.vscode.check_status(req)
        self.assertEqual(rtn, True)

class TestBadUrl(unittest.TestCase):
    def test_bad_url(self):
        req = Mock()
        req.status_code = 404
        rtn = plugins.vscode.check_status(req)
        self.assertEqual(rtn, False)

class TestRedirectHeader(unittest.TestCase):
    def test_redirect_header(self):
        req = Mock()
        req.headers = {'Accept-Ranges': 'bytes', 
                       'Age': '60176', 
                       'Cache-Control': 'public, max-age=86400', 
                       'Content-Type': 'application/octet-stream', 
                       'Date': 'Thu, 30 May 2024 09:49:29 GMT',
                       'Etag': '"0xC8425B813CF3D597C5F7E751ABB71C9FFCC78E6A39662936C7A15544A4047001"',
                       'Last-Modified': 'Tue, 07 May 2024 06:07:27 GMT',
                       'Server': 'ECAcc (lpl/EF5C)',
                       'X-Cache': 'HIT',
                       'X-Ms-ApiVersion': 'Distribute 1.2',
                       'X-Ms-Region': 'prod-neu-z1',
                       'Content-Length': '101857382',
                       'Content-Disposition': "attachment; filename=code_1.89.1-1715060508_amd64.deb; filename*=UTF-8''code_1.89.1-1715060508_amd64.deb"
                       }
        rtn = plugins.vscode.redirect_header(req)
        self.assertEqual(rtn, "code_1.89.1-1715060508_amd64.deb")

class TestQualifyFilename(unittest.TestCase):
    def test_qualify_filename(self):
        rtn = plugins.vscode.qualify_filename("path/", "filename")
        self.assertEqual(rtn, "path/filename")
        rtn = plugins.vscode.qualify_filename("path", "filename")
        self.assertEqual(rtn, "path/filename")

class TestCheckFile(unittest.TestCase):
    def test_check_file(self):
        rtn = plugins.vscode.check_file("test.file")
        self.assertEqual(rtn, False)
        with open("test.file", "w") as filehandle:
            filehandle.write("test data")
        rtn = plugins.vscode.check_file("test.file")
        self.assertEqual(rtn, True)
        os.remove("test.file")

class TestGetFile(unittest.TestCase):
    def test_get_file(self):
        rtn = plugins.vscode.get_file("http://www.example.com", "test.file", 600, True)
        self.assertEqual(rtn, "curl --no-progress-meter --max-time 600 --write-out %{exitcode} --output test.file 'http://www.example.com' 2>&1")

yaml_vscode = """
- 
  name: bookworm
  mirrors:
    - bookworm-main
  plugins:
    - vscode:
        url: https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64
        path: /media/thumb/aptly/vscode
        timeout: 600
"""

class TestLoadPlugin(unittest.TestCase):
    def test_load_plugin(self):
        sys.path.append(sys.path[0] + SEPARATOR + 'plugins')
        mod = import_module("vscode", False)
        self.assertIsNotNone(mod)
        self.assertIsInstance(mod, object)

class TestPublishVscode(unittest.TestCase):
    def test_yaml(self):
        (timestamp, logfile, rtn) = get_parse_output(yaml_vscode)
        self.assertIn("aptly mirror update bookworm-main >> " + logfile + " 2>&1", rtn)
        self.assertIn("aptly snapshot create bookworm-main-" + timestamp + 
                      " from mirror bookworm-main >> " + logfile + " 2>&1" , rtn)
        self.assertIn("aptly repo add vscode ", rtn)
        self.assertIn("aptly snapshot create vscode-" + timestamp + 
                      " from repo vscode >> " + logfile + " 2>&1" , rtn)
        self.assertIn("aptly snapshot merge -latest bookworm-" + timestamp 
                      + " bookworm-main-" + timestamp + " vscode-"
                      + timestamp + " >> " + logfile + " 2>&1", rtn)
        self.assertIn("aptly publish drop bookworm >> " + logfile + " 2>&1", rtn)
        self.assertIn("aptly publish snapshot -distribution=bookworm bookworm-"
                       + timestamp + " >> " + logfile + " 2>&1", rtn)

if __name__ == '__main__':
    if exists("test.file"):
        # Die if there is a danger of clobbering someone else's file.
        raise Exception("test.file already exists. Delete it manually before running this test. But be sure that won't cause problems for someone else.")
    else:
        unittest.main()
