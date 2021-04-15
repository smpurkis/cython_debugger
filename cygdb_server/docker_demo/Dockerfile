FROM ubuntu:18.04
RUN apt-get update
RUN apt-get install -y python python-dev python-dbg python3.8 python3.8-dev python3.8-dbg gdb
CMD gdb --version
CMD /bin/bash
RUN git clone https://github.com/smpurkis/cython_debugger.git
WORKDIR ./cython_debugger/cygdb_server
RUN pip install -r requirements.txt
CMD python Cygdb_server.py