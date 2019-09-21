import libtmux
import socket
import os
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--num_jp", help="number of jupyter notebooks to start", type=int)
parser.add_argument("--name_sess", help="name of session", type=str)
parser.add_argument("--num_win_to_kill", help="number of env you want to kill", type=int)
args = parser.parse_args()

s = libtmux.Server()
def start(num_users, base_dir='./'):
    #start N jupyter notebooks
    k = s.new_session(args.name_sess)
    for i in tqdm(range(num_users)):
        portNum = 8000+i
        mypath = './'+str(i)
        if not os.path.isdir(mypath):
            os.makedirs(mypath)
        name = 'env'+str(i)
        ses = s.set_environment(name,str(i))
        w = k.new_window(window_name='window'+str(i))
        pane = w.panes[0]
        token = 'a'*i
        command = 'jupyter notebook --ip {} --port {} --no-browser --NotebookApp.token={} --NotebookApp.notebook_dir={}'.format('127.0.0.1',str(portNum),str(token),mypath)
        pane.send_keys(command)
    pass
    

def stop(session_name, num):
    #kill window
    name = 'env' + str(num)
    targetWin = 'window' + str(num)
    session = s.find_where({"session_name": session_name})
    session.remove_environment(name)
    session.kill_window(target_window=targetWin)
    print (name + ' removed')
    pass


def stop_all(session_name):
    #kill session
    s.kill_session(session_name)
    print(session_name + ' killed')
    pass

start(args.num_jp)
stop(args.name_sess, args.num_win_to_kill)
stop_all(args.name_sess)
