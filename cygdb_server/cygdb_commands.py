import time
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
        self.command = command
        self.gdb = GdbController(command=command)
        self.trace = []
        self.frame = None
        self.breakpoints = []
        self.current_breakpoint = None

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

    def add_breakpoint(self, fn="", filename="", module="", lineno=""):
        lineno = str(lineno)
        stem = Path(filename).stem
        if len(fn) > 0:
            self.breakpoints.append(dict(
                type="fn",
                name=fn
            ))
            resp = self.gdb.write(f"cy break {fn}")
            # self.next()
        elif len(filename) > 0 and len(lineno) > 0:
            self.breakpoints.append(dict(
                type="file",
                filename=Path(filename).stem,
                lineno=lineno
            ))
            resp = self.gdb.write(f"cy break {stem}:{lineno}")
            # self.next()
        else:
            return None

        # resp = self.print_output(resp)
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

    def determine_python_type(self, var):
        class_pattern = r"\<\w+ '(.*)'\>"
        resp = self.exec(f"type({var})")
        # assert len(resp) == 1
        match = False
        if len(resp) > 0:
            match = re.match(class_pattern, resp[0])
        if match:
            var_type = f"{match.group(1)}"
        else:
            var_type = "Unknown"
        return var_type

    def get_to_next_cython_line(self):
        at_breakpoint = False
        iterations = 0
        while not at_breakpoint and iterations < 1000:
            iterations += 1
            traces = self.backtrace()
            if len(traces) == 0:
                continue
            print("running to next line")
            for bp in self.breakpoints:
                at_breakpoint = False
                if bp["type"] == "fn":
                    for trace in traces:
                        if trace["function_or_object"] == f'{bp["name"]}()':
                            at_breakpoint = True
                            break
                elif bp["type"] == "file":
                    for trace in traces:
                        if f'{trace["filename"].split(".")[0]}:{trace["lineno"]}' == f'{bp["filename"]}:{bp["lineno"]}':
                            at_breakpoint = True
                            break
                if at_breakpoint:
                    break
                self.next()

    def run(self):
        self.gdb.write(f"cy run")
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
                type_ = f"c {groups[1]}"
                if "py" in type_.lower() or "object" in type_.lower():
                    type_ = self.determine_python_type(name)
            else:
                type_ = self.determine_python_type(name)

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
