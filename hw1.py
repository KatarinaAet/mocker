import libtmux
import os
from tqdm import tqdm
import argparse
import sys

s = libtmux.Server()

def createParser():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    start_parser = subparsers.add_parser('start')
    start_parser.add_argument("--num_jp", help="number of jupyter notebooks to start", type=int)
    start_parser.add_argument("--name_sess", help="name of session", type=str)

    stop_parser = subparsers.add_parser('stop')
    stop_parser.add_argument("--name_sess", help="name of session", type=str)
    stop_parser.add_argument("--num_win_to_kill", help="window number to kill", type=int)

    stop_all_parser = subparsers.add_parser('stop_all')
    stop_all_parser .add_argument("--name_sess", help="name of session", type=str)

    return parser



def start(name_session, num_users, base_dir='./'):
    #start N jupyter notebooks
    k = s.new_session(name_session)
    for i in tqdm(range(num_users)):
        portNum = 8000+i
        mypath = './'
        os.path.join(mypath,str(i))
        if not os.path.isdir(mypath):
            os.makedirs(mypath)
        name = 'env'+str(i)
        ses = s.set_environment(name,str(i))
        w = k.new_window(window_name='window'+str(i))
        pane = w.panes[0]
        token = 'a'*i
        command = 'jupyter notebook --ip {} --port {} --no-browser --NotebookApp.token={} --NotebookApp.notebook_dir={}'.format('127.0.0.1',str(portNum),str(token),mypath)
        pane.send_keys(command)
    

def stop(session_name, num):
    #kill window
    name = 'env' + str(num)
    targetWin = 'window' + str(num)
    session = s.find_where({"session_name": session_name})
    session.remove_environment(name)
    session.kill_window(target_window=targetWin)
    print (name + 'removed')


def stop_all(session_name):
    #kill session
    if not s.has_session(session_name):
        print ('no such session')
    else:
        s.kill_session(session_name)
        print(session_name + 'killed')


if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
 
    if namespace.command == "start":
        start (namespace.name_sess, namespace.num_jp)
    elif namespace.command == "stop":
        stop (namespace.name_sess, namespace.num_win_to_kill)
    elif namespace.command == "stop_all":
        stop_all (namespace.name_sess)
    else:
        print ("Incorrect input!")