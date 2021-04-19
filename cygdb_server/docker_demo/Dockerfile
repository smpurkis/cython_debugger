FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y texinfo python python2-dev python2-dbg python3.8 python3.8-dev python3.8-dbg python3.8-venv python3-distutils python3-apt gdb git wget curl build-essential

RUN mkdir gdb_python2_installation
WORKDIR ./gdb_python2_installation
RUN wget https://ftp.gnu.org/gnu/gdb/gdb-10.1.tar.xz
RUN tar -xJf ./gdb-10.1.tar.xz
WORKDIR ./gdb-10.1
RUN ./configure --with-python=python2
RUN make
RUN make install
WORKDIR ../

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip2-7.py
RUN python3.8 get-pip.py --force-reinstall
RUN python3.8 -m pip --version
RUN python2.7 get-pip2-7.py --force-reinstall
RUN python2.7 -m pip --version
RUN python2.7 -m pip install cython==3.0a6
RUN python3.8 -m pip install cython==3.0a6
RUN python3.8-dbg -m pip install cython==3.0a6

RUN echo 75
RUN git clone https://github.com/smpurkis/cython_debugger.git
WORKDIR ./cython_debugger/cygdb_server
RUN python3.8 -m pip install -r requirements.txt
#WORKDIR /working_folder


#CMD python3.8 Cygdb_terminal.py -p python3.8-dbg -f main.py; /bin/bash
#CMD which gdb; gdb --version; /bin/bash
EXPOSE 3456
#CMD /bin/bash
CMD python3.8 /gdb_python2_installation/cython_debugger/cygdb_server/Cygdb_server.py || /bin/bash
#CMD python3.8 Cygdb_terminal.py -p python3.8-dbg -f main.py; python3.8 Cygdb_server.py; /bin/bash
