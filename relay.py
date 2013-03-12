#!/usr/bin/env python

import ConfigParser
import json
from optparse import OptionParser
import os
import sys

import envoy

LIB_PATH = '/usr/local/lib/relay'
CONF_PATH = os.path.expanduser('~/.relay.conf')

if not os.path.exists(CONF_PATH):
    sys.exit('Relay config file does not exist at %s!' % CONF_PATH)

config = ConfigParser.ConfigParser()
config.read(CONF_PATH)

env = {}

env['relay_user'] = config.get('relay', 'user') 
env['relay_server'] = config.get('relay', 'server')
env['pair_private_key'] = os.path.expanduser(config.get('relay', 'private_key'))
env['pair_public_key'] = os.path.expanduser(config.get('relay', 'public_key'))
env['pair_user'] = config.get('relay', 'pair_user')
env['ports_json'] = os.path.expanduser(config.get('relay', 'ports_json'))
env['bash_profile'] = os.path.expanduser(config.get('relay', 'bash_profile'))

env['lib_path'] = LIB_PATH 
env['forward_agent'] = True

def _parse_options():
    parser = OptionParser(
        usage=("relay [options] <command>[:arg1,arg2=val2,...] ...")
    )

    opts, args = parser.parse_args()
    return parser, opts, args

def _escape_split(sep, argstr):
    """
    Allows for escaping of the separator: e.g. task:arg='foo\, bar'

    It should be noted that the way bash et. al. do command line parsing, those
    single quotes are required.
    """
    escaped_sep = r'\%s' % sep

    if escaped_sep not in argstr:
        return argstr.split(sep)

    before, _, after = argstr.partition(escaped_sep)
    startlist = before.split(sep)  # a regular split is fine here
    unfinished = startlist[-1]
    startlist = startlist[:-1]

    # recurse because there may be more escaped separators
    endlist = _escape_split(sep, after)

    # finish building the escaped value. we use endlist[0] becaue the first
    # part of the string sent in recursion is the rest of the escaped value.
    unfinished += sep + endlist[0]

    return startlist + [unfinished] + endlist[1:]  # put together all the parts

def _parse_arguments(arguments):
    cmds = []
    for cmd in arguments:
        args = []
        kwargs = {}
        if ':' in cmd:
            cmd, argstr = cmd.split(':', 1)
            for pair in _escape_split(',', argstr):
                result = _escape_split('=', pair)
                if len(result) > 1:
                    k, v = result
                    kwargs[k] = v
                else:
                    args.append(result[0])
        cmds.append((cmd, args, kwargs))
    return cmds

def _main():
    try:
        parser, options, arguments = _parse_options()

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
    envoy.run('cat %(bash_profile)s >> ~/.bash_profile' % env)

def create_pairprogrammer_osx():
    """
    Create OSX pair programming user.
    """
    envoy.run('sudo dscl . -create /Users/%(pair_user)s' % env)
    envoy.run('sudo dscl . -create /Users/%(pair_user)s UserShell /bin/bash' % env)
    envoy.run('sudo dscl . -create /Users/%(pair_user)s RealName "%(pair_user)s"' % env)
    envoy.run('sudo dscl . -create /Users/%(pair_user)s UniqueID "1667"' % env)
    envoy.run('sudo dscl . -create /Users/%(pair_user)s PrimaryGroupID 20' % env)

    envoy.run('sudo mkdir -p /Users/%(pair_user)s' % env)
    envoy.run('sudo dscl . -create /Users/%(pair_user)s NFSHomeDirectory /Users/%(pair_user)s' % env)

    envoy.run('sudo dscl . -append /Groups/com.apple.access_ssh GroupMembership %(pair_user)s' % env)

    envoy.run('sudo mkdir -p /Users/%(pair_user)s/.ssh/' % env)
    envoy.run('sudo cp %(pair_public_key)s /Users/%(pair_user)s/.ssh/authorized_keys' % env)
    
    envoy.run('sudo cp %(bash_profile)s /Users/%(pair_user)s/.bash_profile' % env)

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
    envoy.run(str('ssh -i %(pair_private_key)s -N -R 0.0.0.0:%(remote_port)s:localhost:%(local_port)s %(relay_user)s@%(relay_server)s' % env))

def ssh():
    """
    SSH to remote user.
    """
    env['remote_port'] = env['port_map']['22']

    envoy.run('chmod 600 %(pair_private_key)s' % env)
    envoy.run('ssh -i %(pair_private_key)s -p %(remote_port)s %(pair_user)s@%(relay_server)s' % env)

def web():
    """
    Open web browser at remote user's development server.
    """
    env['remote_port'] = env['port_map']['8000']

    envoy.run('open http://%(relay_server)s:%(remote_port)s' % env)

if __name__ == '__main__':
    _main()
