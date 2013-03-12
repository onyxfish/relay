#!/usr/bin/env python

import ConfigParser
import json
from optparse import OptionParser
import os
import shlex
import socket
import subprocess
import sys
import termios
import tty

import paramiko

LIB_PATH = '/usr/local/lib/relay'
CONF_PATH = os.path.expanduser('~/.relay.conf')

env = {}

def _parse_options():
    """
    Read configuration and parse command line options.
    """
    if not os.path.exists(CONF_PATH):
        sys.exit('Relay config file does not exist at %s!' % CONF_PATH)

    config = ConfigParser.ConfigParser()
    config.read(CONF_PATH)

    parser = OptionParser(
        usage=("relay [options] <command>[:arg1,arg2,...] ...")
    )

    parser.add_option('--user',
        dest='relay_user',
        default=config.get('relay', 'user'),
        help='User to connect to the relay server as'
    )

    parser.add_option('--server',
        dest='relay_server',
        default=config.get('relay', 'server'),
        help='Hostname or IP of the relay server'
    )

    parser.add_option('--private-key',
        dest='pair_private_key',
        default=os.path.expanduser(config.get('relay', 'private_key')),
        help='Absolute path to the private SSH key'
    )

    parser.add_option('--public-key',
        dest='pair_public_key',
        default=os.path.expanduser(config.get('relay', 'public_key')),
        help='Absolute path to the public SSH key'
    )

    parser.add_option('--pair-user',
        dest='pair_user',
        default=config.get('relay', 'pair_user'),
        help='Username of the pair programmer account on each developer computer'
    )

    parser.add_option('--ports-json',
        dest='ports_json',
        default=os.path.expanduser(config.get('relay', 'ports_json')),
        help='Absolute path to the port mapping file'
    )

    parser.add_option('--bash-profile',
        dest='bash_profile',
        default=os.path.expanduser(config.get('relay', 'bash_profile')),
        help='Absolute path to a file containing bash aliases to be installed when creating the pair programmer user'
    )

    parser.add_option('--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help='Display verbose output'
    )

    opts, args = parser.parse_args()

    opts.lib_path = LIB_PATH

    return parser, opts, args

def _parse_arguments(arguments):
    """
    Convert fabric-style arguments.

    Partially lifted from fabric: https://github.com/fabric/fabric
    """
    cmds = []
    for cmd in arguments:
        args = []
        kwargs = {}
        if ':' in cmd:
            cmd, argstr = cmd.split(':', 1)
            for pair in argstr.split(','):
                args.append(pair)
        cmds.append((cmd, args, kwargs))
    return cmds

def run(cmd):
    """
    Run a shell command using subprocess.
    """
    cmd = str(cmd)

    if env['verbose']:
        sys.stdout.write('--> %s\n' % cmd)

    cmd_list = shlex.split(cmd)

    p = subprocess.Popen(
        cmd_list,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return p.communicate()

def posix_shell(chan):
    """
    POSIX shell implementation for proxied SSH.

    Lifted from Paramiko examples.
    """
    import select
    
    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = chan.recv(1024)
                    if len(x) == 0:
                        print '\r\n*** EOF\r\n',
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

def _main():
    """
    Execute a series of arbitrary commands.

    Partially lifted from fabric: https://github.com/fabric/fabric
    """
    try:
        parser, options, arguments = _parse_options()
        env.update(vars(options))

        arguments = parser.largs

        if not (arguments):
            parser.print_help()
            sys.exit(0)

        commands_to_run = _parse_arguments(arguments)

        for name, args, kwargs in commands_to_run:
            try:
                func = globals()[name]
            except KeyError:
                sys.stderr.write('Command %s does not exist' % name)
                sys.exit(1)

            func(*args, **kwargs)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.stdout.write('\nQuit\n')

    sys.exit(0)

"""
UTILS
"""

def user(username):
    """
    Set programmer to use for connection.
    """
    if env['verbose']:
        sys.stdout.write('User: %s\n' % username)

    with open(env['ports_json']) as f:
        user_port_maps = json.load(f)
        env['port_map'] = user_port_maps[username]

"""
SETUP
"""

def install_bash_profile():
    """
    Install bash profile aliases for local user.
    """
    run('cat %(bash_profile)s >> ~/.bash_profile' % env)

def create_pairprogrammer_osx():
    """
    Create OSX pair programming user.
    """
    #sys.stdout.write('Creating user "%(pair_users"' % env)

    run('sudo dscl . -create /Users/%(pair_user)s' % env)
    run('sudo dscl . -create /Users/%(pair_user)s UserShell /bin/bash' % env)
    run('sudo dscl . -create /Users/%(pair_user)s RealName "%(pair_user)s"' % env)
    run('sudo dscl . -create /Users/%(pair_user)s UniqueID "1667"' % env)
    run('sudo dscl . -create /Users/%(pair_user)s PrimaryGroupID 20' % env)

    run('sudo mkdir -p /Users/%(pair_user)s' % env)
    run('sudo dscl . -create /Users/%(pair_users NFSHomeDirectory /Users/%(pair_user)s' % env)

    run('sudo dscl . -append /Groups/com.apple.access_ssh GroupMembership %(pair_user)s' % env)

    run('sudo mkdir -p /Users/%(pair_user)s/.ssh/' % env)
    run('sudo cp %(pair_public_key)s /Users/%(pair_user)s/.ssh/authorized_keys' % env)
    
    run('sudo cp %(bash_profile)s /Users/%(pair_user)s/.bash_profile' % env)

def setup():
    install_bash_profile()
    create_pairprogrammer_osx()

"""
SHARING
"""

def share(local_port):
    """
    Share a local port with remote users.
    """
    env['local_port'] = local_port

    try:
        env['remote_port'] = env['port_map'][local_port]
    except KeyError:
        sys.exit('Port mapping does not exist for port %s' % local_port)
    
    sys.stdout.write('Sharing local port %(local_port)s on remote port %(remote_port)s\n' % env)

    run('ssh -i %(pair_private_key)s -N -R 0.0.0.0:%(remote_port)s:localhost:%(local_port)s %(relay_user)s@%(relay_server)s' % env)

def ssh():
    """
    SSH to remote user.
    """
    env['remote_port'] = env['port_map']['22']

    sys.stdout.write('Connecting to SSH session on remote port %(remote_port)s\n' % env)

    run('chmod 600 %(pair_private_key)s' % env)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(
        hostname=env['relay_server'],
        port=int(env['remote_port']),
        username=env['pair_user'],
        key_filename=env['pair_private_key']
    )

    channel = client.invoke_shell()
    posix_shell(channel)

def web():
    """
    Open web browser at remote user's development server.
    """
    env['remote_port'] = env['port_map']['8000']

    sys.stdout.write('Launching browser on remote port %(remote_port)s\n' % env)

    run('open http://%(relay_server)s:%(remote_port)s' % env)

if __name__ == '__main__':
    _main()
