import subprocess as sp
import pexpect as px

BUILD_CMD = "python3-dbg setup.py build_ext --inplace"
RUN_DEBUGGER = "gdb  python3-dbg main.py"
build_outputs = sp.run(BUILD_CMD.split(), stdout=sp.PIPE).stdout.decode()
print(build_outputs)

c = px.spawn(RUN_DEBUGGER, maxread=0)
print(c.read().decode())
c.flush()
c.write("help cy")
p = 0

# #
# sess = sp.Popen(RUN_DEBUGGER.split(), stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=0)
# sess.stdin.flush()
# sess.stdout.flush()
# sess.stderr.flush()
# # sess.wait(timeout=5)
# print(sess.stdout.readable())
# outs = sess.stdout.read()
# sess.stdout.flush()
# print(outs)
# # sess.stdin.write(RUN_DEBUGGER)
# # sess.stdin.flush()
# sess.stdin.write("echo hello".encode())
# sess.stdout.flush()
# print(sess.stdout.read())
# while True:
#     cmd = input("Enter Command: ")
#     sess.stdin.write(cmd.encode())
#     sess.stdout.flush()
#     print(sess.stdout.read())
