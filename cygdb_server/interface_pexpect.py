import pexpect


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
