import json

import requests
from pytest import mark

server_url = "http://127.0.0.1:3456/"

config = {
    "gdb_executable_path": "/usr/local/bin/gdb",
    "python_debug_executable_path": "/usr/bin/python3.8-dbg",
    "gdb_configuration_file": "gdb_configuration_file",
}


@mark.order0
def test_hello_get():
    resp = requests.get(server_url + "hello")
    print(resp)
    print(resp.text)
    assert resp.text == '"Working"'


@mark.order1
def test_hello_post():
    resp = requests.post(server_url + "hello", data=json.dumps({
        "hello": "Sam",
        "test": "eopofmw"
    }))
    print(resp)
    print(resp.text)
    assert resp.text == '"Hello: Sam"'


# @mark.order2
# def test_config_post():
#     resp = requests.post(server_url + "Config", data=json.dumps(config))
#     print(resp)
#     print(resp.text)


@mark.order3
def test_set_file_to_debug():
    resp = requests.post(server_url + "setFileToDebug", data=json.dumps({
        "source": "main.py"
    }))
    print(resp)
    print(resp.text)
    resp = json.loads(resp.text)
    assert resp["source"] == "main.py"
    assert resp["success"] is True
    assert type(resp["output"]) == str


@mark.order4
def test_set_breakpoints_post():
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


@mark.order5
def test_launch_post():
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


@mark.order7
def test_frame_get():
    resp = requests.get(server_url + "Frame")
    print(resp)
    frame = json.loads(resp.text)
    assert len(frame.get("local_variables", [])) == 8
    assert len(frame.get("global_variables", [])) == 12
    assert len(frame.get("trace", [])) == 2


@mark.order8
def test_continue_get():
    resp = requests.get(server_url + "Continue")
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": "demo.pyx",
            "lineno": "27"
        }
    }


@mark.order9
def test_restart_post():
    resp = requests.get(server_url + "Restart")
    print(resp)
    print(resp.text)


@mark.order10
def test_set_file_to_debug2():
    resp = requests.post(server_url + "setFileToDebug", data=json.dumps({
        "source": "main.py"
    }))
    print(resp)
    print(resp.text)


@mark.order11
def test_set_breakpoints_post2():
    resp = requests.post(server_url + "setBreakpoints", data=json.dumps({
        "source": "demo.pyx",
        "breakpoints": [8]
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "source": "demo.pyx",
        "breakpoints": [8]
    }


@mark.order12
def test_launch_post2():
    resp = requests.post(server_url + "Launch", data=json.dumps({
        "source": "demo.pyx",
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": "demo.pyx",
            "lineno": "8"
        }
    }
