relay
========

Magical SSH tunnels for remote developers behind firewalls.

Currently allows for sharing SSH connections (for collaborating in tmux+vim) and for sharing local development webservers.

Install
--------

```
sudo pip install git+https://github.com/nprapps/relay.git
```

Setup
--------

In order to use relay you must have Dropbox installed, syncing to `~/Dropbox` and the `nprapps` shared folder synced to your local computer. This will allow relay to access the pairprogrammer shared keys.

Relay uses a configuration file located at `~/.relay.conf`. A pre-made configuration file is in the Dropbox and should be symlinked to your directory:

```
ln -s ~/Dropbox/nprapps/relay/relay.conf ~/.relay.conf
```

You then need to create a `pairprogrammer` user. This process is automated:

```
relay setup
```

Sharing SSH
------------------

To share your SSH connection (for tmux'ing), open a new terminal (or tab or tmux pane):

```
relay user:$USER share:22
```

Where `$USER` is your username.

To connect to a shared SSH connection:

```
relay user:$USER ssh
```

Where `$USER` is the username of the user sharing the connection.

Sharing development webserver
-----------------------------

To share your local development webserver, open a new terminal (or tab or tmux pane):

```
relay user:$USER share:8000
```

Where `$USER` is your username.

To connect open a shared webserver in your browser:

```
relay user:$USER web
```

Where `$USER` is the username of the user sharing the webserver.


