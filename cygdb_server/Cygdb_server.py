#!/usr/bin/env python

"""
The Cython debugger

The current directory should contain a directory named 'cython_debug', or a
path to the cython project directory should be given (the parent directory of
cython_debug).

Additional gdb args can be provided only if a path to the project directory is
given.
"""
import glob
import logging
import os
import subprocess as sp
import textwrap
from pathlib import Path
from typing import List

import uvicorn
import yaml
from fastapi import FastAPI, Body
from pydantic import BaseModel

from cygdb_commands import CygdbController

logger = logging.getLogger(__name__)


def make_command_file(path_to_debug_info, prefix_code=''):
    pattern = os.path.join(path_to_debug_info,
                           'cython_debug',
                           'cython_debug_info_*')
    debug_files = glob.glob(pattern)

    gdb_cy_configure_path = Path("cython_debug", "gdb_configuration_file")
    gdb_cy_configure_path.parent.mkdir(exist_ok=True)
    f = gdb_cy_configure_path.open("w")
    try:
        f.write(prefix_code)
        f.write(textwrap.dedent('''\
            # This is a gdb command file
            # See https://sourceware.org/gdb/onlinedocs/gdb/Command-Files.html

            set breakpoint pending on
            set print pretty on

            python
            try:
                # Activate virtualenv, if we were launched from one
                import os
                virtualenv = os.getenv('VIRTUAL_ENV')
                if virtualenv:
                    path_to_activate_this_py = os.path.join(virtualenv, 'bin', 'activate_this.py')
                    print("gdb command file: Activating virtualenv: %s; path_to_activate_this_py: %s" % (
                        virtualenv, path_to_activate_this_py))
                    with open(path_to_activate_this_py) as f:
                        exec(f.read(), dict(__file__=path_to_activate_this_py))
                from Cython.Debugger import libcython, libpython
            except Exception as ex:
                from traceback import print_exc
                print("There was an error in Python code originating from the file ''' + str(__file__) + '''")
                print("It used the Python interpreter " + str(sys.executable))
                print_exc()
                exit(1)
            end
            '''))

        path = os.path.join(path_to_debug_info, "cython_debug", "interpreter")
        interpreter_file = open(path)
        try:
            interpreter = interpreter_file.read()
        finally:
            interpreter_file.close()
        f.write("file %s\n" % interpreter)
        f.write('\n'.join('cy import %s\n' % fn for fn in debug_files))
        f.write(textwrap.dedent('''\
            python
            import sys
            try:
                gdb.lookup_type('PyModuleObject')
            except RuntimeError:
                sys.stderr.write(
                    "''' + interpreter + ''' was not compiled with debug symbols (or it was "
                    "stripped). Some functionality may not work (properly).\\n")
            end

            source .cygdbinit
        '''))
    finally:
        f.close()

    return gdb_cy_configure_path


def setup_files(debug_path=".",
                python_debug_executable_path="/usr/bin/python3-dbg"):
    """
    Start the Cython debugger. This tells gdb to import the Cython and Python
    extensions (libcython.py and libpython.py) and it enables gdb's pending
    breakpoints.
    """

    BUILD_CMD = f"{python_debug_executable_path} setup.py build_ext --inplace --force"
    build_outputs = sp.run(BUILD_CMD.split(), stdout=sp.PIPE).stdout.decode()
    print(build_outputs)

    path_to_debug_info = debug_path

    tempfilename = make_command_file(path_to_debug_info)
    return tempfilename


class Config(BaseModel):
    gdb_executable_path: str
    file_path: str
    python_debug_executable_path: str


app = FastAPI()


class CythonServer:
    def __init__(self, config_path=None):
        self.config_path = config_path
        if self.config_path is not None:
            self.config = yaml.safe_load(config_path)
            self.load_config(self.config)
        else:
            self.gdb_executable_path = "/usr/bin/gdb",
            self.gdb_configuration_file = "gdb_configuration_file",
            self.python_debug_executable_path = "/usr/bin/python3-dbg",
            self.file_path = "main.py"
            self.debug_path = "."
        self.cygdb = None

    def load_config(self, config):
        self.gdb_executable_path = config.gdb_executable_path
        self.python_debug_executable_path = config.python_debug_executable_path
        self.file_path = config.file_path

    def setup_tempfilename(self):
        if self.debug_path and self.python_debug_executable_path:
            self.gdb_configuration_file = setup_files(self.debug_path, self.python_debug_executable_path)

    def set_debug_path(self, debug_path):
        self.debug_path = debug_path

    def set_gdb_executable(self, gdb_executable):
        self.gdb_executable_path = gdb_executable

    def set_python_debug_executable(self, python_debug_executable_path):
        self.python_debug_executable_path = python_debug_executable_path

    def set_file_path(self, file_path):
        self.file_path = file_path

    def format_progress(self, resp):
        if len(resp) == 0:
            resp = {
                "ended": True
            }
        else:
            resp = {
                "ended": False,
                "breakpoint": {
                    "filename": resp[-1]["filename"],
                    "lineno": resp[-1]["lineno"]
                }
            }
        return resp

    def continue_debugger(self):
        resp = self.cygdb.cont()
        return self.format_progress(resp)

    def run_debugger(self):
        self.gdb_configuration_file = setup_files(self.debug_path, self.python_debug_executable_path)
        self.cmd = [self.gdb_executable_path, "--nx", "--interpreter=mi3", "--quiet", '-command',
                    self.gdb_configuration_file.as_posix(),
                    "--args",
                    self.python_debug_executable_path,
                    self.file_path]
        print(" ".join(self.cmd))

        resp = self.cygdb.run()
        return self.format_progress(resp)


cython_server = CythonServer()


@app.post("/config")
def load_config_post(config: Config):
    cython_server.load_config(config)
    cython_server.debug_path = "."
    cython_server.setup_tempfilename()
    cython_server.cmd = [cython_server.gdb_executable_path, "--nx", "--interpreter=mi3", "--quiet", '-command',
                         cython_server.gdb_configuration_file.as_posix(),
                         "--args",
                         cython_server.python_debug_executable_path,
                         cython_server.file_path]

    cython_server.cygdb = CygdbController(command=cython_server.cmd)
    print(cython_server.cygdb)


@app.post("/hello")
def hello(hello: str = Body(...), test: str = Body(...)):
    return "Hello: " + hello


@app.get("/hello")
def hello():
    return "Working"


@app.post("/setBreakpoints")
def set_breakpoints(source: str = Body(...), breakpoints: List[int] = Body(...)):
    valid_breakpoints = []
    for lineno in breakpoints:
        valid = cython_server.cygdb.add_breakpoint(
            filename=source,
            lineno=lineno
        )
        if valid:
            valid_breakpoints.append(lineno)
    return {
        "source": source,
        "breakpoints": breakpoints
    }


@app.post("/Launch")
def run_debugger(source: str = Body(..., embed=True)):
    return cython_server.run_debugger()


@app.get("/Continue")
def continue_debugger():
    return cython_server.continue_debugger()


@app.get("/Frame")
def get_frame():
    return cython_server.cygdb.frame


if __name__ == '__main__':
    # config = dict(
    #     gdb_executable_path="/usr/bin/gdb",
    #     tempfilename="gdb_configuration_file",
    #     python_debug_executable_path="/usr/bin/python3-dbg",
    #     file_path="main.py"
    # )
    # config_path = Path("cygdb.yaml")
    # yaml.dump(config, config_path.open("w"))
    uvicorn.run(app, port=3456, debug=True)
