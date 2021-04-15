FROM ubuntu:18.04
RUN apt-get update
RUN apt-get install -y python python-dev python-dbg python-pip python3.8 python3.8-dev python3.8-dbg python3.8-venv python3-distutils python3-apt gdb git curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.8 get-pip.py --force-reinstall
RUN python3.8 -m pip --version
RUN git clone https://github.com/smpurkis/cython_debugger.git
WORKDIR ./cython_debugger/cygdb_server
RUN pip install -r requirements.txt
CMD python3.8 Cygdb_server.py