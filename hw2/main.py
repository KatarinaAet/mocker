#!/home/ekaterina/anaconda3/bin/python


import shutil
import random
import requests
import json
import os
import tarfile
import os
import uuid
import json
from pprint import pprint
import subprocess
import traceback
#from pyroute2.ipdb.main import IPDB
from pyroute2 import IPDB, NetNS
from cgroups import Cgroup
from cgroups.user import create_user_cgroups
from pychroot import Chroot
import argparse
from terminaltables import AsciiTable


def create_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='Commands',
                                       description='Команды',
                                       help='Команды для работы с mocker')

    init_parser = subparsers.add_parser('init', help='создать образ контейнера используя указанную директорию как '
                                                     'корневую. Возвращает в stdout id созданного образа.')
    init_parser.add_argument('directory', metavar='init-directory', default='./mocker_images',
                             type=str, help='Директория для создания контейнера')
    init_parser.set_defaults(func=parse_init)

    pull_parser = subparsers.add_parser('pull', help='скачать последний (latest) тег указанного образа с Docker Hub. '
                                                     'Возвращает в stdout id созданного образа.')
    pull_parser.add_argument('image', type=str, metavar='pull-image', help='Имя образа')
    pull_parser.set_defaults(func=parse_pull)

    rmi_parser = subparsers.add_parser('rmi', help='удаляет ранее созданный образ из локального хранилища.')
    rmi_parser.add_argument('imageid', type=int, metavar='rmi-imageid', help='ID образа')
    rmi_parser.set_defaults(func=parse_rmi)

    images_parser = subparsers.add_parser('images', help='выводит список локальных образов')
    images_parser.set_defaults(func=parse_images)

    ps_parser = subparsers.add_parser('ps', help='выводит список локальных образов')
    ps_parser.set_defaults(func=parse_ps)

    run_parser = subparsers.add_parser('run', help='создает контейнер из указанного image_id и запускает его с '
                                                   'указанной командой')
    run_parser.add_argument('imageid', type=str, metavar='run-imageid', help='ID образа')
    #run_parser.add_argument('command', type=str, metavar='run-command', help='Команда')
    run_parser.set_defaults(func=parse_run)

    exec_parser = subparsers.add_parser('exec', help='запускает указанную команду внутри уже запущенного указанного '
                                                     'контейнера')
    exec_parser.add_argument('containerid', type=int, metavar='exec-containerid', help='ID контейнера')
    exec_parser.add_argument('command', type=str, metavar='exec-command', help='Команда')
    exec_parser.set_defaults(func=parse_exec)

    logs_parser = subparsers.add_parser('logs', help='выводит логи указанного контейнера')
    logs_parser.add_argument('containerid', type=int, metavar='log-containerid', help='ID контейнера')
    logs_parser.set_defaults(func=parse_logs)

    rm_parser = subparsers.add_parser('rm', help='удаляет ранее созданный контейнер')
    rm_parser.add_argument('containerid', type=int, metavar='rm-containerid', help='ID контейнера')
    rm_parser.set_defaults(func=parse_rm)

    commit_parser = subparsers.add_parser('commit', help='удаляет ранее созданный контейнер')
    commit_parser.add_argument('containerid', type=int, metavar='commit-containerid', help='ID контейнера')
    commit_parser.add_argument('imageid', type=int, metavar='commit-imageid', help='ID образа')
    commit_parser.set_defaults(func=parse_commit)

    return parser


def parse_init(args):
    init(args.directory)


def parse_pull(args):
    pull('library', args.image)


def parse_rmi(args):
    rmi(args.imageid)


def parse_images(args):
	list_images()


def parse_ps(args):
    print('Not implemented')


def parse_run(args):
	run(args.imageid)
    #print('Not implemented')


def parse_exec(args):
    print('Not implemented')


def parse_logs(args):
    print('Not implemented')


def parse_rm(args):
    print('Not implemented')


def parse_commit(args):
    print('Not implemented')

def get_images():
    images = [['name', 'version', 'size', 'file']]

    for image_file in os.listdir('./mocker_images'):
        if image_file.endswith('.json'):
            with open(os.path.join('./mocker_images', image_file), 'r') as json_f:
                image = json.loads(json_f.read())
            image_base = os.path.join('./mocker_images', image_file.replace('.json', ''), 'layers')
            size = sum(os.path.getsize(os.path.join(image_base, f)) for f in
                        os.listdir(image_base)
                        if os.path.isfile(os.path.join(image_base, f)))
            images.append([image['name'], image['tag'], sizeof_fmt(size), image_file])
    return images


def list_images():
    images = get_images()
    table = AsciiTable(images)
    print(table.table)

def sizeof_fmt(num, suffix='B'):
    ''' Credit : http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size '''
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
    list_images()


def init(src):
    img_id = random.randint(0, 1000)
    folder_img = os.path.join(path_to_images, 'image_' + str(img_id))
    try:
        shutil.copytree(src, folder_img)
        print("Directory copied to " + folder_img)
        print("Image id: " + str(img_id))
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def rmi(image_id):
    path_to_delete = path_to_images + '/image_' + str(image_id)
    try:
        shutil.rmtree(path_to_delete)
        print(path_to_delete + "removed")
    except:
        print('Error while deleting directory')


def auth(library, image):
    # request a v2 token
    token_req = requests.get(
        'https://auth.docker.io/token?service=registry.docker.io&scope=repository:%s/%s:pull'
        % ('library', image))
    return token_req.json()['token']


def get_headers(library, image):
    headers = {'Authorization': 'Bearer %s' % auth(library, image)}
    return headers


def get_manifest(library, image):
    # get the image manifest
    print("Fetching manifest for %s:%s..." % (image, 'latest'))

    manifest = requests.get('%s/%s/%s/manifests/%s' %
                            (registry_base, 'library', image, 'latest'),
                            headers=get_headers(library, image))

    return manifest.json()


def pull(library, image):
    headers = get_headers(library, image)
    manifest = get_manifest(library, image)
    image_name_friendly = manifest['name'].replace('/', '_')

    with open(os.path.join(path_to_images, image_name_friendly + '.json'), 'w') as cache:
        cache.write(json.dumps(manifest))
        # save the layers to a new folder
    dl_path = os.path.join(path_to_images, image_name_friendly, 'layers')
    if not os.path.exists(dl_path):
        os.makedirs(dl_path)

        # fetch each unique layer
    layer_sigs = [layer['blobSum'] for layer in manifest['fsLayers']]
    unique_layer_sigs = set(layer_sigs)

    # setup a directory with the image contents
    contents_path = os.path.join(dl_path, 'contents')
    if not os.path.exists(contents_path):
        os.makedirs(contents_path)

        # download all the parts
    for sig in unique_layer_sigs:
        print('Fetching layer %s..' % sig)
        url = '%s/%s/%s/blobs/%s' % (registry_base, 'library',
                                     image, sig)
        local_filename = os.path.join(dl_path, sig) + '.tar'

        r = requests.get(url, stream=True, headers=get_headers(library, image))
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

            # list some of the contents..
        with tarfile.open(local_filename, 'r') as tar:
            for member in tar.getmembers()[:10]:
                print('- ' + member.name)
            print('...')

            tar.extractall(str(contents_path))
    print('Pulled successfully')

def run(image_name):
    ip_last_octet = 103
    images = get_images()

    match = [i[3] for i in images if i[0] == image_name][0]

    target_file = os.path.join('./mocker_images', match)
    with open(target_file) as tf:
        image_details = json.loads(tf.read())
        # setup environment details
        state = json.loads(image_details['history'][0]['v1Compatibility'])

        # Extract information about this container
        env_vars = state['config']['Env']
        start_cmd = subprocess.list2cmdline(state['config']['Cmd'])
        working_dir = state['config']['WorkingDir']

        id = uuid.uuid1()

        # unique-ish name
        name = 'c_' + str(id.fields[5])[:4]

        # unique-ish mac
        mac = str(id.fields[5])[:2]

        layer_dir = os.path.join('./mocker_images', match.replace('.json', ''), 'layers', 'contents')

        with IPDB() as ipdb:
            veth0_name = 'veth0_'+name
            veth1_name = 'veth1_'+name
            netns_name = 'netns_'+name
            bridge_if_name = 'bridge0'

            existing_interfaces = ipdb.interfaces.keys()

            # Create a new virtual interface
            with ipdb.create(kind='veth', ifname=veth0_name, peer=veth1_name) as i1:
                i1.up()
                if bridge_if_name not in existing_interfaces:
                    ipdb.create(kind='bridge', ifname=bridge_if_name).commit()
                    i1.set_target('master', bridge_if_name)

            # Create a network namespace
            NetNs.create(netns_name)

            # move the bridge interface into the new namespace
            with ipdb.interfaces[veth1_name] as veth1:
                veth1.net_ns_fd = netns_name

            # Use this network namespace as the database
            ns = IPDB(nl=NetNS(netns_name))
            with ns.interfaces.lo as lo:
                lo.up()
            with ns.interfaces[veth1_name] as veth1:
                veth1.address = "02:42:ac:11:00:{0}".format(mac)
                veth1.add_ip('10.0.0.{0}/24'.format(ip_last_octet))
                veth1.up()
                ns.routes.add({
                'dst': 'default',
                'gateway': '10.0.0.1'}).commit()

            try:
                # setup cgroup directory for this user
                user = os.getlogin()
                create_user_cgroups(user)

                # First we create the cgroup and we set it's cpu and memory limits
                cg = Cgroup(name)
                cg.set_cpu_limit(50) 
                cg.set_memory_limit(500)

                # Then we a create a function to add a process in the cgroup
                def in_cgroup():
                    try:
                        pid = os.getpid()
                        cg = Cgroup(name)
                        for env in env_vars:
                            print('Setting ENV %s' % env)
                            os.putenv(*env.split('=', 1))

                        # Set network namespace
                        netns.setns(netns_name)

                        # add process to cgroup
                        cg.add(pid)

                        os.chroot(layer_dir)
                        if working_dir != '':
                            print("Setting working directory to %s" % working_dir)
                            os.chdir(working_dir)
                    except Exception as e:
                        traceback.print_exc()
                        print("Failed to preexecute function")
                        print(e)
                cmd = start_cmd
                print('Running "%s"' % cmd)
                process = subprocess.Popen(cmd, preexec_fn=in_cgroup, shell=True)
                process.wait()
                print(process.stdout)
                print(process.stderr)
            except Exception as e:
                traceback.print_exc()
                print(e)
            finally:
                print('Finalizing')
                NetNS(netns_name).close()
                netns.remove(netns_name)
                ipdb.interfaces[veth0_name].remove()
                print('done')


path_to_images = '/home/ekaterina/documents/mocker_images'

registry_base = 'https://registry-1.docker.io/v2'
library = 'library'

parser = create_parser()

namespace = parser.parse_args()


if not vars(namespace):
    parser.print_usage()
else:
    namespace.func(namespace)
