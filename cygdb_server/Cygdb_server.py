import logging
import subprocess as sp
import textwrap
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel

from gdb_interface import CygdbController

logger = logging.getLogger(__name__)

MOUNTED_PROJECT_FOLDER = "/project_folder"

WORKING_FOLDER = "./working_folder"


def recopy_mounted_folder_to_working_folder():
    cmd = f"rm -rdf {WORKING_FOLDER}"
    print(cmd)
    sp.call(cmd.split())

    cmd = f"cp -r {MOUNTED_PROJECT_FOLDER}/ {WORKING_FOLDER}"
    print(cmd)
    sp.call(cmd.split())


recopy_mounted_folder_to_working_folder()


def make_command_file(path_to_debug_info, prefix_code=''):
    debug_files = [debug_file.as_posix() for debug_file in
                   Path(WORKING_FOLDER, path_to_debug_info, "cython_debug", ).glob("cython_debug_info_*")]

    gdb_cy_configure_path = Path(WORKING_FOLDER, "cython_debug", "gdb_configuration_file")
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

        path = Path(WORKING_FOLDER, path_to_debug_info, "cython_debug", "interpreter")
        assert path.exists()
        interpreter_file = path.open()
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

    BUILD_CMD = f"{python_debug_executable_path} setup.py build_ext --inplace"
    print(BUILD_CMD)
    build_outputs = sp.run(BUILD_CMD.split(" "), cwd=WORKING_FOLDER, stdout=sp.PIPE, stderr=sp.PIPE)

    stdout = build_outputs.stdout.decode()
    stderr = build_outputs.stderr.decode()
    print("stdout", stdout)
    print("stderr", stderr)
    if "Error compiling Cython file" in stderr or "doesn't match any files" in stderr:
        return stderr, False

    return stdout, True


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
        self.file_path = Path(WORKING_FOLDER, file_path).as_posix()
        # return self.setup_files()

    def setup_files(self):
        if self.debug_path and self.python_debug_executable_path:
            output, successful_compile = cythonize_files(self.python_debug_executable_path)
            if successful_compile:
                self.gdb_configuration_file = make_command_file(self.debug_path)
            return output, successful_compile

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

    def cythonize_files(self):
        output, successful_compile = self.setup_files()
        if not successful_compile:
            return {
                "success": False,
                "output": output
            }
        else:
            return {
                "success": True,
                "output": output
            }

    def run_debugger(self):
        self.cmd = [self.gdb_executable_path, "--nx", "--interpreter=mi3", "--quiet", '-command',
                    self.gdb_configuration_file.as_posix(),
                    "--args",
                    self.python_debug_executable_path,
                    self.file_path]

        print(" ".join(self.cmd))
        self.cygdb.spawn_gdb(self.cmd)

        self.cygdb.add_breakpoints()
        resp = self.cygdb.run()
        return self.format_progress(resp)

    def restart_debugger(self):
        recopy_mounted_folder_to_working_folder()
        self.cygdb.exit_gdb()
        self.cygdb.clear_all()
        self.cygdb.gdb.start_new_process()


cython_server = CythonServer()
cython_server.python_debug_executable_path = "/usr/bin/python3.8-dbg"
cython_server.gdb_executable_path = "/usr/local/bin/gdb"
cython_server.debug_path = "."


@app.get("/Restart")
def restart():
    global cython_server
    cython_server.restart_debugger()
    return


@app.post("/setFileToDebug")
def set_file_to_debug(source: str = Body(..., embed=True)):
    cython_server.file_to_debug(source)
    return {
        "success": True,
        "source": source,
    }


@app.post("/hello")
def hello(hello: str = Body(...), test: str = Body(...)):
    return "Hello: " + hello


@app.get("/hello")
def hello():
    return "Working"


@app.get("/compileFiles")
def compile_files():
    return cython_server.cythonize_files()


@app.post("/setBreakpoints")
def set_breakpoints(source: str = Body(...), breakpoints: List[int] = Body(...)):
    cython_server.cygdb = CygdbController()
    valid_breakpoints = []
    for lineno in breakpoints:
        valid = cython_server.cygdb.add_prints_to_file(
            filename=source,
            lineno=lineno,
            full_path=Path(WORKING_FOLDER, source).as_posix()
        )
        print(Path(WORKING_FOLDER, source).as_posix())
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


@app.post("/installRequirements")
def install_requirements(requirements: str = Body(..., embed=True)):
    user_requirements_file = Path("user_requirements.txt")
    if user_requirements_file.exists():
        user_requirements_file.unlink()
    user_requirements_file.write_text(requirements)
    pip_install_cmd = f"python3.8-dbg -m pip install -r user_requirements.txt --force --no-cache"
    print(pip_install_cmd)
    build_outputs = sp.run(pip_install_cmd.split(), stdout=sp.PIPE, stderr=sp.PIPE)

    stdout = build_outputs.stdout.decode()
    stderr = build_outputs.stderr.decode()
    return_code = build_outputs.returncode

    if return_code != 0:
        return dict(
            success=False,
            output=stderr
        )

    return dict(
        success=True,
        output=stdout
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=3456)
