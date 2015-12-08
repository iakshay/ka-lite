from splinter import Browser
import subprocess
import signal
from time import sleep
import os
import glob
import os.path as osp
import psutil

HOME = "http://localhost:8008/"
DEVNULL = open(os.devnull, 'wb')

# src - https://github.com/fabianp/memory_profiler/blob/master/mprof#L49-L104
def get_profile_filenames(args):
    """Return list of profile filenames.
    Parameters
    ==========
    args (list)
        list of filename or integer. An integer is the index of the
        profile in the list of existing profiles. 0 is the oldest,
        -1 in the more recent.
        Non-existing files cause a ValueError exception to be thrown.
    Returns
    =======
    filenames (list)
        list of existing memory profile filenames. It is guaranteed
        that an given file name will not appear twice in this list.
    """
    profiles = glob.glob("mprofile_??????????????.dat")
    profiles.sort()

    if args is "all":
        filenames = copy.copy(profiles)
    else:
        filenames = []
        for arg in args:
            if arg == "--":  # workaround
                continue
            try:
                index = int(arg)
            except ValueError:
                index = None
            if index is not None:
                try:
                    filename = profiles[index]
                except IndexError:
                    raise ValueError("Invalid index (non-existing file): %s" % arg)

                if filename not in filenames:
                    filenames.append(filename)
            else:
                if osp.isfile(arg):
                    if arg not in filenames:
                        filenames.append(arg)
                elif osp.isdir(arg):
                    raise ValueError("Path %s is a directory" % arg)
                else:
                    raise ValueError("File %s not found" % arg)

    # Add timestamp files, if any
    for filename in reversed(filenames):
        parts = osp.splitext(filename)
        timestamp_file = parts[0] + "_ts" + parts[1]
        if osp.isfile(timestamp_file) and timestamp_file not in filenames:
            filenames.append(timestamp_file)

    return filenames

def kill_with_children(pid):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):  # or parent.children() for recursive=False
        child.send_signal(signal.SIGTERM)
    parent.send_signal(signal.SIGTERM)

def visit_home(browser):
    browser.visit(HOME)

def play_video(browser):
    browser.visit(HOME + '/learn/khan/college-admissions/get-started/introduction-ca/sal-khans-story-college-admissions/')

def record_usage(browser, fn):
    server = subprocess.Popen(['mprof', 'run', 'python', 'kalitectl.py', 'start', '--foreground'], stdout=DEVNULL, stderr=DEVNULL)
    # wait for server to start
    sleep(5)
    fn(browser)
    kill_with_children(server.pid)
    sleep(5)
    filename =  get_profile_filenames(['-1'])[0]
    memory_usage = []
    peak_usage = 0
    with open(filename) as f:
        for line in f:
            buf = line.split(' ')

            if len(buf) == 3:
                mem = float(buf[1])
                ts = float(buf[2])
                memory_usage.append((mem, ts))

                if mem > peak_usage:
                    peak_usage = mem
    os.remove(filename)
    return peak_usage

if __name__ == '__main__':
    memory_usage = {}
    with Browser('phantomjs') as browser:
        memory_usage['visit_home'] = record_usage(browser, visit_home)
        memory_usage['play_video'] = record_usage(browser, play_video)

    print memory_usage
