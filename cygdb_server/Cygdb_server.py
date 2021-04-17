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


def cythonize_files(python_debug_executable_path="/usr/bin/python3-dbg"):
    """
    Start the Cython debugger. This tells gdb to import the Cython and Python
    extensions (libcython.py and libpython.py) and it enables gdb's pending
    breakpoints.
    """

    BUILD_CMD = f"{python_debug_executable_path} setup.py build_ext --inplace --force"
    build_outputs = sp.run(BUILD_CMD.split(), stdout=sp.PIPE, stderr=sp.PIPE)
    stdout = build_outputs.stdout.decode()
    stderr = build_outputs.stderr.decode()
    if "Error compiling Cython file" in stderr:
        return stderr.split("\n"), False
    print(stdout)
    print(stderr)

    return stdout.split("\n"), True


class Config(BaseModel):
    gdb_executable_path: str
    python_debug_executable_path: str


app = FastAPI()


class CythonServer:
    def __init__(self):
        self.gdb_executable_path = None
        self.gdb_configuration_file = None
        self.python_debug_executable_path = None
        self.file_path = None
        self.debug_path = None
        self.cygdb = None

    def file_to_debug(self, file_path):
        self.file_path = Path("/project_folder", file_path).as_posix()
        return self.setup_files()

    def setup_files(self):
        if self.debug_path and self.python_debug_executable_path:
            self.gdb_configuration_file = make_command_file(self.debug_path)
            return cythonize_files(
                self.python_debug_executable_path
            )

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
        output, successful_compile = self.setup_files()
        if not successful_compile:
            return {
                "success": False,
                "stderr": output
            }
        self.cmd = [self.gdb_executable_path, "--nx", "--interpreter=mi3", "--quiet", '-command',
                    self.gdb_configuration_file.as_posix(),
                    "--args",
                    self.python_debug_executable_path,
                    self.file_path]
        print(" ".join(self.cmd))

        resp = self.cygdb.run()
        return self.format_progress(resp)

    def restart_debugger(self):
        self.cygdb.exit_gdb()
        self.cygdb.gdb.spawn_new_gdb_subprocess()


cython_server = CythonServer()
cython_server.python_debug_executable_path = "/usr/bin/python3.8-dbg"
cython_server.gdb_executable_path = "/usr/local/bin/gdb"
cython_server.gdb_configuration_file = "cython_debug/gdb_configuration_file"
cython_server.debug_path = "."


@app.post("/setFileToDebug")
def set_file_to_debug(source: str = Body(..., embed=True)):
    output, successful_compile = cython_server.file_to_debug(source)
    if not successful_compile:
        return {
            "success": False,
            "source": source,
            "output": output
        }
    cython_server.cmd = [cython_server.gdb_executable_path, "--nx", "--interpreter=mi3", "--quiet", '-command',
                         cython_server.gdb_configuration_file.as_posix(),
                         "--args",
                         cython_server.python_debug_executable_path,
                         cython_server.file_path]

    cython_server.cygdb = CygdbController(command=cython_server.cmd)
    print(cython_server.cygdb)
    return {
        "success": True,
        "source": source,
        "output": output
    }


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
def run_debugger():
    return cython_server.run_debugger()


@app.get("/Continue")
def continue_debugger():
    return cython_server.continue_debugger()


@app.get("/Frame")
def get_frame():
    return cython_server.cygdb.frame


@app.get("/Restart")
def restart():
    global cython_server
    cython_server.restart_debugger()
    return


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=3456)
