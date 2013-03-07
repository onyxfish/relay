#!/usr/bin/env python

import ConfigParser
import json
import os
import sys

from fabric.api import *

LIB_PATH = '/usr/local/lib/relay'
CONF_PATH = os.path.expanduser('~/.relay.conf')

if not os.path.exists(CONF_PATH):
    sys.exit('Relay config file does not exist at %s!' % CONF_PATH)

config = ConfigParser.ConfigParser()
config.read(CONF_PATH)

env.relay_user = config.get('relay', 'user') 
env.relay_server = config.get('relay', 'server')
env.pair_private_key = os.path.expanduser(config.get('relay', 'private_key'))
env.pair_public_key = os.path.expanduser(config.get('relay', 'public_key'))
env.pair_user = config.get('relay', 'pair_user')
env.ports_json = os.path.expanduser(config.get('relay', 'ports_json'))
env.bash_profile = os.path.expanduser(config.get('relay', 'bash_profile'))

env.lib_path = LIB_PATH 
env.forward_agent = True

"""
UTILS
"""

def user(username):
    """
    Set programmer to use for connection.
    """
    with open(env.ports_json) as f:
        user_port_maps = json.load(f)
        env.port_map = user_port_maps[username]

"""
SETUP
"""

def install_bash_profile():
    """
    Install bash profile aliases for local user.
    """
    local('cat %(bash_profile)s >> ~/.bash_profile' % env)

def create_pairprogrammer_osx():
    """
    Create OSX pair programming user.
    """
    local('sudo dscl . -create /Users/%(pair_user)s' % env)
    local('sudo dscl . -create /Users/%(pair_user)s UserShell /bin/bash' % env)
    local('sudo dscl . -create /Users/%(pair_user)s RealName "%(pair_user)s"' % env)
    local('sudo dscl . -create /Users/%(pair_user)s UniqueID "1667"' % env)
    local('sudo dscl . -create /Users/%(pair_user)s PrimaryGroupID 20' % env)

    local('sudo mkdir -p /Users/%(pair_user)s' % env)
    local('sudo dscl . -create /Users/%(pair_user)s NFSHomeDirectory /Users/%(pair_user)s' % env)

    with settings(warn_only=True):
        local('sudo dscl . -append /Groups/com.apple.access_ssh GroupMembership %(pair_user)s' % env)

    local('sudo mkdir -p /Users/%(pair_user)s/.ssh/' % env)
    local('sudo cp %(pair_public_key)s /Users/%(pair_user)s/.ssh/authorized_keys' % env)
    
    local('sudo cp %(bash_profile)s /Users/%(pair_user)s/.bash_profile' % env)

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
    require('port_map', provided_by=[user])

    env.local_port = local_port
    env.remote_port = env.port_map[local_port]

    local('ssh -i %(pair_private_key)s -N -R 0.0.0.0:%(remote_port)s:localhost:%(local_port)s %(relay_user)s@%(relay_server)s' % env)

def ssh():
    """
    SSH to remote user.
    """
    require('port_map', provided_by=[user])

    env.remote_port = env.port_map['22']

    local('chmod 600 %(pair_private_key)s' % env)
    local('ssh -i %(pair_private_key)s -p %(remote_port)s %(pair_user)s@%(relay_server)s' % env)

def web():
    """
    Open web browser at remote user's development server.
    """
    require('port_map', provided_by=[user])

    env.remote_port = env.port_map['8000']

    local('open http://%(relay_server)s:%(remote_port)s' % env)


