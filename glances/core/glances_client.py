#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Glances - An eye on your system
#
# Copyright (C) 2014 Nicolargo <nicolas@nicolargo.com>
#
# Glances is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Glances is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Manage the Glances' client 
"""

# Import system libs
import sys
import socket
import json

# Import Glances libs
from glances.core.glances_globals import __version__
from glances.outputs.glances_curses import glancesCurses
from glances.core.glances_stats import GlancesStatsClient

try:
    # Python 2
    from xmlrpclib import ServerProxy, ProtocolError
except ImportError:
    # Python 3
    from xmlrpc.client import ServerProxy, ProtocolError


class GlancesClient():
    """
    This class creates and manages the TCP client
    """

    def __init__(self,
                 args=None,
                 server_address="localhost", server_port=61209,
                 username="glances", password="",
                 config=None):
        # Build the URI
        if (password != ""):
            uri = 'http://%s:%s@%s:%d' % (username, password, server_address, server_port)
        else:
            uri = 'http://%s:%d' % (server_address, server_port)

        # Try to connect to the URI
        try:
            self.client = ServerProxy(uri)
        except Exception as e:
            print("{} {} ({})".format(_("Error: creating client socket"), uri, e))
            sys.exit(2)

        # Store the arg/config
        self.args = args
        self.config = config

    def login(self):
        """
        Logon to the server
        """
        try:
            client_version = self.client.init()
        except socket.error as err:
            print("{} ({})".format(_("Error: Connection to server failed"), err))
            sys.exit(2)
        except ProtocolError as err:
            if (str(err).find(" 401 ") > 0):
                print("{} ({})".format(_("Error: Connection to server failed"), _("Bad password")))
            else:
                print("{} ({})".format(_("Error: Connection to server failed"), err))
            sys.exit(2)

        # Test if client and server are "compatible"
        if (__version__[:3] == client_version[:3]):
            # Init stats and limits
            self.stats = GlancesStatsClient()
            self.stats.set_plugins(json.loads(self.client.getAllPlugins()))
            self.stats.load_limits(self.config)

            # Init screen
            self.screen = glancesCurses(args=self.args)

            # Debug
            # print "Server version: {}\nClient version: {}\n".format(__version__, client_version)
            return True
        else:
            return False

    def update(self):
        """
        Get stats from server
        Return the client/server connection status:
        - Connected: Connection OK
        - Disconnected: Connection NOK
        """        
        try:
            server_stats = json.loads(self.client.getAll())
        except socket.error as e:
            # Client can not get server stats
            return "Disconnected"
        else:
            # Put it in the internal dict
            self.stats.update(server_stats)
            return "Connected"

    def serve_forever(self):
        """
        Main client loop
        """
        while True:
            # Update the stats
            cs_status = self.update()

            # Update the screen
            self.screen.update(self.stats, cs_status=cs_status)

    def close(self):
        """
        End of the client session
        """
        pass