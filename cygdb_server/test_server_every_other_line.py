import json
from pathlib import Path

import requests

server_url = "http://127.0.0.1:3456/"



def test_install_requirements():
    requirements = Path("requirements.txt").read_text()
    resp = requests.post(server_url + "installRequirements", data=json.dumps({
        "requirements": requirements
    }))
    print(resp)
    print(resp.text)
    resp = json.loads(resp.text)
    assert resp["success"] is True
    assert type(resp["output"]) == str


def test_set_file_to_debug():
    resp = requests.post(server_url + "setFileToDebug", data=json.dumps({
        "source": "main.py"
    }))
    print(resp)
    print(resp.text)
    resp = json.loads(resp.text)
    assert resp["source"] == "main.py"
    assert resp["success"] is True
    # assert type(resp["output"]) == str


def test_set_breakpoints_post():
    breakpoints = list(range(16, 28))
    resp = requests.post(server_url + "setBreakpoints", data=json.dumps({
        "source": "demo.pyx",
        "breakpoints": breakpoints
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "source": "demo.pyx",
        "breakpoints": breakpoints
    }


def test_compile_files():
    resp = requests.get(server_url + "compileFiles")
    print(resp)
    print(resp.text)
    text = json.loads(resp.text)
    assert text["success"] is True
    assert type(text["output"]) == str


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
            "lineno": "16"
        }
    }


def test_continue_get():
    breakpoint_lines_set = [str(i) for i in range(18, 39, 2)]
    for i in breakpoint_lines_set:
        print()
        print(i)
        resp = requests.get(server_url + "Continue")
        print(resp)
        print(resp.text)
        text = json.loads(resp.text)
        assert text["ended"] is False
        assert type(text["breakpoint"]) == dict
        assert list(text["breakpoint"].keys()) == ["filename", "lineno"]
        assert abs(int(text["breakpoint"]["lineno"]) - int(i)) <= 1

# def test_frame_get():
#     resp = requests.get(server_url + "Frame")
#     print(resp)
#     frame = json.loads(resp.text)
#     assert len(frame.get("local_variables", [])) == 8
#     assert len(frame.get("global_variables", [])) == 12
#     assert len(frame.get("trace", [])) == 2
