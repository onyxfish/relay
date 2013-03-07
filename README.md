relay
========

Meta-magical SSH tunnels for remote developers behind firewalls.

Currently allows for sharing SSH connections (for collaborating in tmux+vim) and for sharing local development webservers.

Install
--------

Relay can be installed in a virtualenv, but we recommend installing it with sudo so it is always available:

```
sudo pip install relay
```

General setup
-------------

*nprapps users see the next section*

Relay uses a configuration file located at `~/.relay.conf`. Create this file with contents such as:

```
[relay]
user = ubuntu
server = relay_server.your_domain.com
private_key = /path/to/your/private_key
public_key = /path/to/your/public_key.pub
pair_user = relay
ports_json = /path/to/your/ports.json
```

`ports.json` is a mapping of user's local ports to remote ports on the server, so that users will never collide when creating SSH tunnels. Create this file with contents such as:

```
{
    "chris": {
        "22": "2222",
        "8000": "8000"
    },
    "katie": {
        "22": "2223",
        "8000": "8001"
    },
}
```

You then need to create a `pairprogrammer` user. This process is automated:

```
relay setup
```

NPRApps setup
-----------------

Pre-baked configuration files are in our Dropbox folder. You must have Dropbox installed, syncing to `~/Dropbox` and the `nprapps` shared folder synced to your local computer.

```
ln -s ~/Dropbox/nprapps/relay/relay.conf ~/.relay.conf
relay setup
```

Sharing SSH
------------------

To share your SSH connection (for tmux'ing), open a new terminal (or tab or tmux pane):

```
relay user:$USER share:22
```

Where `$USER` is your username in `ports.json`.

To connect to a shared SSH connection:

```
relay user:$USER ssh
```

Where `$USER` is the username in `ports.json` of the user sharing the connection.

Sharing development webserver
-----------------------------

To share your local development webserver, open a new terminal (or tab or tmux pane):

```
relay user:$USER share:8000
```

Where `$USER` is your username in `ports.json`.

To connect open a shared webserver in your browser:

```
relay user:$USER web
```

Where `$USER` is the username in `ports.json` of the user sharing the webserver.


