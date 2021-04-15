#!/usr/bin/env python

"""
The Cython debugger

The current directory should contain a directory named 'cython_debug', or a
path to the cython project directory should be given (the parent directory of
cython_debug).

Additional gdb args can be provided only if a path to the project directory is
given.
"""
import fcntl
import glob
import logging
import optparse
import os
import subprocess as sp
import sys
import textwrap
from pygdbmi.gdbcontroller import GdbController
from pathlib import Path
from cygdb_commands import CygdbController

logger = logging.getLogger(__name__)


def make_command_file(path_to_debug_info, prefix_code=''):
    pattern = os.path.join(path_to_debug_info,
                           'cython_debug',
                           'cython_debug_info_*')
    debug_files = glob.glob(pattern)

    if not debug_files:
        sys.exit('%s.\nNo debug files were found in %s. Aborting.' % (
            usage, os.path.abspath(path_to_debug_info)))

    gdb_cy_configure_path = Path("cython_debug", "gdb_configure_file")
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


usage = "Usage: cygdb [options] [PATH [-- GDB_ARGUMENTS]]"



def main(path_to_debug_info=None, gdb_argv=None):
    """
    Start the Cython debugger. This tells gdb to import the Cython and Python
    extensions (libcython.py and libpython.py) and it enables gdb's pending
    breakpoints.

    path_to_debug_info is the path to the Cython build directory
    gdb_argv is the list of options to gdb
    """
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--gdb-executable",
                      dest="gdb", default='gdb',
                      help="gdb executable to use [default: gdb]")
    parser.add_option("--debug-path", "-d",
                      dest="debug_path", default=".")
    parser.add_option("--python-executable", "-p",
                      dest="python", default="python")
    parser.add_option("--file", "-f",
                      dest="file", default="main.py")

    BUILD_CMD = "python3.8-dbg setup.py build_ext --inplace"
    build_outputs = sp.run(BUILD_CMD.split(), stdout=sp.PIPE).stdout.decode()
    print(build_outputs)

    (options, args) = parser.parse_args()
    path_to_debug_info = options.debug_path

    tempfilename = make_command_file(path_to_debug_info)
    cmd = [options.gdb, "--nx", "--interpreter=mi3", "--quiet", '-command', tempfilename.as_posix(), "--args", options.python,
           options.file]
    print(" ".join(cmd))

    cygdb = CygdbController(command=cmd)

    # set breakpoints
    # cygdb.breakpoint(fn="baz")
    cygdb.add_breakpoint(filename="demo", lineno="17")
    cygdb.add_breakpoint(filename="demo", lineno="20")

    cygdb.run()
    p = 0
    cygdb.cont()
    cygdb.get_globals()
    p = 0
    cygdb.cont()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.next()
    # cygdb.get_locals()


    # with open(tempfilename) as tempfile:
    #     p = sp.Popen([options.gdb, "--nx", "--quiet", '-command', tempfilename.as_posix(), "--args", options.python,
    #                   options.file],
    #                  stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=0)
    #     make_non_blocking(p.stdout)
    #     make_non_blocking(p.stderr)
    #     time.sleep(0.5)
    #     raw_output = p.stdout.read()
    #     cleaned_output = clean_output(raw_output)
    #     print(cleaned_output)
    #
    #     # cmd = "help"
    #     # p.stdout.flush()
    #     # p.stdin.write(cmd.encode())
    #     # p.stdin.flush()
    #     # time.sleep(0.1)
    #     # out = p.stdout.read().decode()
    #     # print(out)
    #     while True:
    #         try:
    #             cmd = input("CyGdb > ") + "\n"
    #             # cmd = "help\n"
    #             p.stdin.write(cmd.encode())
    #             p.stdin.flush()
    #             time.sleep(0.5)
    #             raw_output = p.stdout.read()
    #             cleaned_output = clean_output(raw_output)
    #             p.stdout.flush()
    #             print(cleaned_output)
    #
    #         except Exception as e:
    #             print(e)
    #         except KeyboardInterrupt as ke:
    #             print(ke)
    #             break


def clean_output(raw_stdout):
    """
    decode and remove the "(gdb) >" last output
    """
    decoded_list = raw_stdout.decode().split("\n")
    if "gdb" in decoded_list[-1].lower():
        cleaned = "\n".join(decoded_list[:-1])
    else:
        cleaned = "\n".join(decoded_list[:-1])
    return cleaned


def make_non_blocking(file_obj):
    """make file object non-blocking
    Windows doesn't have the fcntl module, but someone on
    stack overflow supplied this code as an answer, and it works
    http://stackoverflow.com/a/34504971/2893090"""

    fcntl.fcntl(file_obj, fcntl.F_SETFL, os.O_NONBLOCK)


if __name__ == '__main__':
    main()
