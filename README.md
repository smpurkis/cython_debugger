# cython_debugger

Work in progress, to hook up cygdb to a server client framework for Cython debugging (like VS code)

Update 26/11/21 - This was an attempt to make a Cython debugger. I did manage to get a working version of connecting gdb to cython code, using the same method as cygdb. However, there are so many odd and difficult dependencies, e.g. it still relying on dead Python 2.7, that I've decided to no longer pursue this endeavour as much as I would have like to finish it.
I wish anyone who has a similar idea luck in making it work.
