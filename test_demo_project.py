import json
from pathlib import Path

import requests

server_url = "http://127.0.0.1:3456/"

file_to_debug = "monte_carlo_simulation.pyx"
source = "run_file.py"


def test_install_requirements():
    requirements = Path("demo_project/requirements.txt").read_text()
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
        "source": source
    }))
    print(resp)
    print(resp.text)
    resp = json.loads(resp.text)
    assert resp["source"] == source
    assert resp["success"] is True
    # assert type(resp["output"]) == str


def test_set_breakpoints_post():
    breakpoints = [34, 40]
    resp = requests.post(server_url + "setBreakpoints", data=json.dumps({
        "source": file_to_debug,
        "breakpoints": breakpoints
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "source": file_to_debug,
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
        "source": file_to_debug,
    }))
    print(resp)
    print(resp.text)
    assert json.loads(resp.text) == {
        "ended": False,
        "breakpoint": {
            "filename": file_to_debug,
            "lineno": "34"
        }
    }


def test_continue_get():
    breakpoint_lines_set = ["41"]
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
