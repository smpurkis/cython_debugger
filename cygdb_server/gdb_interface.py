import ast
from pathlib import Path

import pexpect
import regex as re


class Frame:
    def __init__(self, local_variables=None,
                 global_variables=None,
                 lineno=None,
                 filename=None,
                 function_name=None,
                 trace=None,
                 process_id=None,
                 thread_id=None):
        self.local_variables = None
        self.global_variables = []
        self.local_variables = []
        self.lineno = lineno
        self.filename = filename
        self.function_name = function_name
        self.trace = trace
        self.process_id = process_id
        self.thread_id = thread_id


class CygdbController:
    def __init__(self):
        self.breakpoint_lines = {}
        self.trace = []
        self.frame = None
        self.breakpoints = []
        self.current_breakpoint = 0

    def spawn_gdb(self, cmd):
        self.gdb = Process(cmd=cmd)

    def clear_all(self):
        self.breakpoints = []
        self.current_breakpoint = 0
        self.trace = []
        self.frame = None
        self.breakpoint_lines = {}

    def exit_gdb(self):
        self.gdb.exit()

    def get_locals(self):
        resp = self.gdb.write("cy locals")
        return self.format_pexpect_output(resp)

    def next(self):
        resp = self.gdb.write("cy next")
        resp = self.format_pexpect_output(resp)
        return resp

    def correct_line_number(self, lineno, full_path, to_breakpoint=False):
        full_path = Path(full_path)
        lines = full_path.open().read().split("\n")
        if not self.breakpoint_lines.get(full_path, False):
            self.breakpoint_lines[full_path] = list(range(1, len(lines) + 1))
        linenos = self.breakpoint_lines[full_path]
        # pprint(linenos)
        corrected_lineno = linenos.index(int(lineno))
        print("corrected_lineno: ", corrected_lineno, full_path, lineno, to_breakpoint)
        check = 0
        for i in range(len(lines)):
            if "breakpoint" not in str(linenos[i]):
                check += 1
            if linenos[i] == int(lineno):
                check = str(check)
                break
        # return str(check)
        print("check/old value: ", check)
        if to_breakpoint:
            corrected_lineno = corrected_lineno
            # assert "breakpoint" in str(linenos[corrected_lineno]-1)
            return str(corrected_lineno)
        else:
            return str(corrected_lineno)

    def add_print_to_file(self, filename="", lineno="", full_path=None):
        file_path = Path(full_path)
        lines = file_path.open().read().split("\n")
        lineno_corrected = self.correct_line_number(lineno, full_path)
        lineno_int = max(int(lineno_corrected) - 1, 0)
        code_on_line_to_break = lines[lineno_int + 1]
        check_line = re.match(r"^\W+(\S+)", code_on_line_to_break)
        if check_line is None:
            return False
        leading_spaces = re.match(r"^(\W+)", code_on_line_to_break)
        if leading_spaces is not None:
            leading_spaces = leading_spaces.group(0)
        else:
            leading_spaces = ""
        line_to_add = f"{leading_spaces}print()  # empty print to prevent Cython optimizing out this line"
        lines.insert(lineno_int + 1, line_to_add)
        self.breakpoint_lines[full_path].insert(lineno_int + 1, f"breakpoint-{lineno}")
        # from pprint import pprint
        # pprint(self.breakpoint_lines[full_path])
        lines_with_i = [[i + 1, line] for i, line in enumerate(lines)]
        # pprint(lines_with_i)
        text = "\n".join(lines)
        file_path.unlink(missing_ok=False)
        fp = file_path.open("w")
        fp.write(text)
        fp.close()
        return True

    def add_breakpoints(self):
        break_cmd = "cy break " + " ".join([f"{bp['filename']}:{self.correct_line_number(bp['lineno'], bp['full_path'])}" for bp in self.breakpoints])
        resp = self.gdb.write(break_cmd)
        # TODO Check the resp of adding breakpoint to verify set correctly

    def add_prints_to_file(self, filename="", lineno="", full_path=""):
        lineno = str(lineno)
        stem = Path(filename).stem
        if len(filename) > 0 and len(lineno) > 0:
            valid_line = self.add_print_to_file(filename, lineno, Path(full_path))
            if not valid_line:
                return valid_line
            self.breakpoints.append(dict(
                type="file",
                filename=Path(filename).stem,
                lineno=lineno,
                full_path=full_path
            ))
            lineno = self.correct_line_number(lineno, full_path)
        else:
            return False
        return True

    def get_frame(self):
        frame = Frame()
        frame.local_variables = self.format_locals(self.get_locals())
        frame.trace = self.backtrace()
        frame.global_variables = self.format_globals(self.get_globals())
        self.frame = frame
        return self.frame

    @staticmethod
    def format_backtrace(resp):
        backtrace_stack = []
        trace_line_pattern = r"^(?:\W+)?(\w+)\W+(.*) in (.*) at (.*\/)?(.*):(\w+)(\W+(\w+)\W+(.*))?"
        resp = "".join(resp).split("#")
        resp = [r.rstrip() for r in resp]
        for trace in resp:
            match = re.match(trace_line_pattern, trace)
            if match is None:
                continue
            else:
                groups = match.groups()
            backtrace = dict(
                filename=groups[4],
                lineno=groups[5],
                code=groups[7].replace("\\\"", '"') if groups[7] is not None else None,
                function_or_object=groups[2],
                memory_address=groups[1],
            )
            if groups[3] != "":
                backtrace["file_parent"] = groups[3]
            backtrace_stack.append(backtrace)

        return backtrace_stack

    def step(self):
        resp = self.gdb.write("cy step")
        resp = self.format_pexpect_output(resp)
        return resp

    def backtrace(self):
        resp = self.gdb.write(f"cy bt")
        resp = self.format_pexpect_output(resp)
        resp = self.format_backtrace(resp)
        return resp

    def get_list(self):
        resp = self.gdb.write(f"cy list")
        return self.format_pexpect_output(resp)

    def exec(self, cmd):
        resp = self.gdb.write(f"cy exec {cmd}")
        resp = self.format_pexpect_output(resp)
        return resp

    def determine_python_type(self, name, value=None):
        var_type = "Unknown"
        if value is None:
            class_pattern = r"^\<\w+ \'(.*)\'\>"
            resp = self.exec(f"type({name})")
            # assert len(resp) == 1
            match = False
            if len(resp) > 0:
                match = re.match(class_pattern, resp[0])
            if match:
                var_type = f"{match.group(1)}"
            else:
                var_type = "Unknown"
        else:
            try:
                decoded_value = ast.literal_eval(value)
                var_type = str(type(decoded_value))
            except Exception as e:
                print(e)
        return var_type

    def cont(self):
        resp = self.gdb.write("cy cont")
        resp = self.gdb.write("cy cont")
        self.get_frame()
        print("trace", self.frame.trace)
        return self.frame.trace

    def run(self):
        resp = self.gdb.write(f"cy run")
        resp = self.gdb.write(f"cy cont")
        self.get_frame()
        return self.frame.trace

    @staticmethod
    def format_pexpect_output(responses):
        relevant_responses = []
        for resp in responses:
            if resp == "":
                continue
            if resp[0] == "~":
                resp = resp.replace("~\"", "").replace("\\n\"", "")
                relevant_responses.append(resp)
            elif resp[0] == "<":
                relevant_responses.append(resp)
        return relevant_responses

    def format_locals(self, variable_list):
        new_variable_list = []
        for var in variable_list:

            type_value_pattern = r"(\w+)\W+= (?:(?:\((.*)?\) )?(.*)|(\[.*\])|(\{.*\}))"
            groups = re.match(type_value_pattern, var).groups()
            name = groups[0]

            if groups[2] is not None:
                value = groups[2]
            else:
                value = "Unknown"

            if groups[1] is not None:
                type_ = groups[1]
                if "Py" in type_ and "Object" in type_:
                    type2_ = self.determine_python_type(name)
                    if type2_.lower() != "unknown":
                        type_ = type2_
                else:
                    type_ = f"cy {groups[1]}"
            else:
                type_ = self.determine_python_type(name, value)

            var = dict(
                name=name,
                type=type_,
                value=value
            )
            new_variable_list.append(var)
        return new_variable_list

    def get_globals(self):
        resp = self.gdb.write("cy globals")
        resp = self.format_pexpect_output(resp)
        try:
            resp.remove('Python globals:')
            resp.remove('C globals:')
        except ValueError as e:
            pass
        return resp

    def format_globals(self, global_list):
        new_global_list = []
        for var in global_list:

            type_value_pattern = r"^\W+(\w+)\W+=\s+(.*)"
            groups = re.match(type_value_pattern, var)

            if groups is None:
                continue

            groups = groups.groups()
            name = groups[0]

            if groups[1] is not None:
                name = groups[0]
                value = groups[1]
            else:
                value = "Unknown"

            var = dict(
                name=name,
                value=value
            )
            new_global_list.append(var)
        return new_global_list

    def command(self, cmd):
        resp = self.gdb.write(cmd)
        return self.format_pexpect_output(resp)


class Process:
    def __init__(self, cmd):
        if type(cmd) == list:
            cmd = " ".join(cmd)
        self.cmd = cmd
        self.start_process(cmd)

    def start_process(self, cmd):
        self.proc = pexpect.spawn(cmd)
        self.write()

    def exit(self):
        self.proc.close(force=True)

    def start_new_process(self):
        self.exit()
        self.start_process(self.cmd)

    def write(self, command=None, first=False):
        if command:
            print("CMD to GDB: ", command)
            self.proc.sendline(command)
        resp = b""
        while True:
            try:
                letter = self.proc.read_nonblocking(size=1, timeout=5)
            except pexpect.exceptions.TIMEOUT as e:
                print(e)
                break
            resp += letter
            if b"(gdb) \r\n" in resp[-8:]:
                if first:
                    first = False
                    continue
                break
        resp = resp.decode()
        resp = resp.replace("\\e", "").replace("[94m", "").replace("[39;49;00m", "").replace(
            "[96m", "").replace("[92m", "").replace("[33m", "").replace("[90m", "").strip("\\n")
        return_count = resp.count("\r\n")
        new_line_count = resp.count("\\n")
        print(resp)
        if return_count > new_line_count:
            resp = resp.split("\r\n")
        else:
            resp = resp.split("\\n")
        return resp


if __name__ == '__main__':
    cmd = "/usr/local/bin/gdb --nx --quiet --interpreter=mi3 -command working_folder2/cython_debug/gdb_configuration_file --args /usr/bin/python3.8-dbg working_folder2/main.py"

    proc = Process(cmd)
    resp = proc.write("cy break demo:16")
    assert len(resp) > 7
    resp2 = proc.write("cy break demo:18")
    assert len(resp) > 7
    resp3 = proc.write("cy break demo:20")
    assert len(resp) > 7
    resp4 = proc.write("cy break demo:22")
    assert len(resp) > 7
    resp5 = proc.write("cy run")
    assert len(resp) > 7
    resp6 = proc.write("cy cont")
    assert len(resp) > 7
    resp7 = proc.write("cy cont")
    assert len(resp) > 7
    resp8 = proc.write("cy cont")
    assert len(resp) > 7
    p = 0
