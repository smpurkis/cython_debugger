import json

import requests

server_url = "http://127.0.0.1:3456/"

config = {
    "file_path": "main.py",
    "gdb_executable_path": "/usr/bin/gdb",
    "python_debug_executable_path": "/usr/bin/python3-dbg",
    "gdb_configuration_file": "gdb_configuration_file",
}

resp = requests.post(server_url + "config", data=json.dumps(config))
print(resp)
print(resp.text)

resp = requests.post(server_url + "items", data=json.dumps({
    "number": 9
}))
print(resp)
print(resp.text)

resp = requests.post(server_url + "hello", data=json.dumps({
    "hello": "qqefew",
    "test": "eopofmw"
}))
print(resp)
print(resp.text)
