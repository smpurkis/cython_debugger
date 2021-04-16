import json
import time
from pprint import pprint

import requests

def test_pipeline():
    server_url = "http://127.0.0.1:3456/"

    config = {
        "file_path": "main.py",
        "gdb_executable_path": "/usr/local/bin/gdb",
        "python_debug_executable_path": "/usr/bin/python3.8-dbg",
        "gdb_configuration_file": "gdb_configuration_file",
    }

    resp = requests.post(server_url + "config", data=json.dumps(config))
    print(resp)
    print(resp.text)

    resp = requests.post(server_url + "hello", data=json.dumps({
        "hello": "qqefew",
        "test": "eopofmw"
    }))
    print(resp)
    print(resp.text)

    resp = requests.post(server_url + "hello", data=json.dumps({
        "hello": "qqefew",
        "test": "eopofmw"
    }))
    print(resp)
    print(resp.text)

    resp = requests.post(server_url + "setBreakpoints", data=json.dumps({
        "source": "demo.pyx",
        "breakpoints": [22, 25]
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "source": "demo.pyx",
        "breakpoints": [22, 25]
    }

    resp = requests.post(server_url + "Launch", data=json.dumps({
        "source": "demo.pyx",
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": "demo.pyx",
            "lineno": "22"
        }
    }

    resp = requests.get(server_url + "Frame")
    print(resp)
    pprint(json.loads(resp.text))
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": "demo.pyx",
            "lineno": "22"
        }
    }

    resp = requests.get(server_url + "Continue")
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": "demo.pyx",
            "lineno": "25"
        }
    }
