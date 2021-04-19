import ast
from pathlib import Path

import regex as re

from pygdbmi.gdbcontroller import GdbController


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
    def __init__(self, command):
        self.breakpoint_lines = {}
        self.command = command
        self.gdb = GdbController(command=command)
        self.trace = []
        self.frame = None
        self.breakpoints = []
        self.current_breakpoint = None

    def clear_all(self):
        self.breakpoints = []
        self.current_breakpoint = None
        self.trace = []
        self.frame = None
        self.breakpoint_lines = {}

    def exit_gdb(self):
        self.gdb.exit()

    def get_locals(self):
        resp = self.gdb.write("cy locals")
        return self.print_output(resp)

    def next(self):
        resp = self.gdb.write("cy next")
        resp = self.print_output(resp)
        return resp

    def cont(self):
        resp = self.gdb.write("cy cont")
        resp = self.print_output(resp)
        # self.next()
        # self.get_to_next_cython_line()
        self.get_frame()
        return self.frame.trace

    def correct_line_number(self, lineno, full_path):
        full_path = Path(full_path)
        lines = full_path.open().read().split("\n")
        if not self.breakpoint_lines.get(full_path, False):
            self.breakpoint_lines[full_path] = list(range(1, len(lines) + 1))
        linenos = self.breakpoint_lines[full_path]
        corrected_lineno = 0

        for i in range(len(linenos)):
            if "breakpoint" not in str(linenos[i]):
                corrected_lineno += 1
            if linenos[i] == int(lineno):
                return str(corrected_lineno)
        raise Exception(f"Breakpoint {lineno} in {full_path} not found!")

    def add_print_to_file(self, filename="", lineno="", full_path=None):
        file_path = Path(full_path)
        lines = file_path.open().read().split("\n")
        lineno_corrected = self.correct_line_number(lineno, full_path)
        lineno_int = max(int(lineno_corrected) - 1, 0)
        code_on_line_to_break = lines[lineno_int]
        check_line = re.match(r"^\W+(\S+)", code_on_line_to_break)
        if check_line is None:
            return False
        leading_spaces = re.match(r"^(\W+)", code_on_line_to_break)
        if leading_spaces is not None:
            leading_spaces = leading_spaces.group(0)
        else:
            leading_spaces = ""
        line_to_add = f"{leading_spaces}print()  # empty print to prevent Cython optimizing out this line"
        lines.insert(lineno_int, line_to_add)
        self.breakpoint_lines[full_path].insert(lineno_int, f"breakpoint-{lineno}")
        from pprint import pprint
        pprint(self.breakpoint_lines[full_path])
        lines_with_i = [[i+1, line] for i, line in enumerate(lines)]
        pprint(lines_with_i)
        text = "\n".join(lines)
        file_path.unlink(missing_ok=False)
        fp = file_path.open("w")
        fp.write(text)
        fp.close()
        return True

    def add_breakpoint(self, filename="", lineno="", full_path=""):
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
            resp = self.gdb.write(f"cy break {stem}:{lineno}")
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
        trace_line_pattern = r"(?:\W+)?(\w+)\W+(.*) in (.*) at (.*\/)?(.*):(\w+)\W+(\w+)\W+(.*)"
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
                code=groups[7].replace("\\\"", '"'),
                function_or_object=groups[2],
                memory_address=groups[1],
            )
            if groups[3] != "":
                backtrace["file_parent"] = groups[3]
            backtrace_stack.append(backtrace)

        return backtrace_stack

    def step(self):
        resp = self.gdb.write("cy step")
        resp = self.print_output(resp)
        return resp

    def backtrace(self):
        resp = self.gdb.write(f"cy bt")
        resp = self.print_output(resp)
        resp = self.format_backtrace(resp)
        return resp

    def get_list(self):
        resp = self.gdb.write(f"cy list")
        return self.print_output(resp)

    def exec(self, cmd):
        resp = self.gdb.write(f"cy exec {cmd}")
        resp = self.print_output(resp)
        return resp

    def determine_python_type(self, name, value=None):
        var_type = "Unknown"
        if value is None:
            class_pattern = r"\<\w+ '(.*)'\>"
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

    def get_to_next_cython_line(self):
        at_breakpoint = False
        iterations = 0
        while not at_breakpoint and iterations < 50:
            iterations += 1
            traces = self.backtrace()
            if len(traces) == 0:
                if iterations > 10:
                    raise Exception(f"Over allowed iterations: {iterations}")
                continue
            print("running to next line")
            for bp in self.breakpoints:
                at_breakpoint = False
                if bp["type"] == "file":
                    for trace in traces:
                        corrected_lineno = self.correct_line_number(bp["lineno"], bp["full_path"])
                        if f'{trace["filename"].split(".")[0]}:{trace["lineno"]}' == f'{bp["filename"]}:{corrected_lineno}':
                            at_breakpoint = True
                            break
                if at_breakpoint:
                    break
                self.next()

    def run(self):
        self.gdb.write(f"cy run", timeout_sec=1)
        self.get_to_next_cython_line()
        self.get_frame()
        return self.frame.trace

    @staticmethod
    def print_output(responses):
        formatted_resp = []
        for resp in responses:
            # print(resp)
            if resp["type"] in ["console", "output"]:
                res = resp["payload"].replace("\\e", "").replace("[94m", "").replace("[39;49;00m", "").replace(
                    "[96m", "").replace("[92m", "").replace("[33m", "").replace("[90m", "").strip("\\n")
                res = "\n".join(res.split("\\n"))
                print(res)
                formatted_resp.append(res)
        return formatted_resp

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
        resp = self.print_output(resp)
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
            groups = re.match(type_value_pattern, var).groups()
            name = groups[0]

            if groups[1] is not None:
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
        return self.print_output(resp)
