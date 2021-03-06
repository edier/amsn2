# -*- coding: utf-8 -*-
#
# amsn - a python client for the WLM Network
#
# Copyright (C) 2008 Dario Freddi <drf54321@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import profile
from amsn2 import gui
from amsn2 import protocol
import papyon
from views import *
from contactlist_manager import *
from conversation_manager import *
from oim_manager import *
from theme_manager import *
from personalinfo_manager import *
from event_manager import *


class aMSNCore(object):
    def __init__(self, options):
        """
        Create a new aMSN Core. It takes an options class as argument
        which has a variable for each option the core is supposed to received.
        This is easier done using optparse.
        The options supported are :
           options.account = the account's username to use
           options.password = the account's password to use
           options.front_end = the front end's name to use
           options.debug = whether or not to enable debug output
        """
        self._event_manager = aMSNEventManager(self)
        self._profile_manager = profile.aMSNProfileManager()
        self._options = options
        self._gui_name = self._options.front_end
        self._gui = gui.GUIManager(self, self._gui_name)
        self._loop = self._gui.gui.aMSNMainLoop(self)
        self._main = self._gui.gui.aMSNMainWindow(self)
        self._skin_manager = self._gui.gui.SkinManager(self)
        self._theme_manager = aMSNThemeManager()
        self._contactlist_manager = aMSNContactListManager(self)
        self._oim_manager = aMSNOIMManager(self)
        self._conversation_manager = aMSNConversationManager(self)
        self._personalinfo_manager = aMSNPersonalInfoManager(self)

        self.p2s = {papyon.Presence.ONLINE:"online",
                    papyon.Presence.BUSY:"busy",
                    papyon.Presence.IDLE:"idle",
                    papyon.Presence.AWAY:"away",
                    papyon.Presence.BE_RIGHT_BACK:"brb",
                    papyon.Presence.ON_THE_PHONE:"phone",
                    papyon.Presence.OUT_TO_LUNCH:"lunch",
                    papyon.Presence.INVISIBLE:"hidden",
                    papyon.Presence.OFFLINE:"offline"}

        if self._options.debug:
            import logging
            logging.basicConfig(level=logging.DEBUG)

    def run(self):
        self._main.show();
        self._loop.run();


    def mainWindowShown(self):
        # TODO : load the profiles from disk and all settings
        # then show the login window if autoconnect is disabled

        self._main.setTitle("aMSN 2 - Loading")


        splash = self._gui.gui.aMSNSplashScreen(self, self._main)
        image = ImageView()
        image.load("Filename","/path/to/image/here")

        splash.setImage(image)
        splash.setText("Loading...")
        splash.show()

        login = self._gui.gui.aMSNLoginWindow(self, self._main)

        profile = None
        if self._options.account is not None:
            if self._profile_manager.profileExists(self._options.account):
                profile = self._profile_manager.getProfile(self._options.account)
            else:
                profile = self._profile_manager.addProfile(self._options.account)
                profile.save = False
            if self._options.password is not None:
                profile.password = self._options.password

        else:
            for prof in self._profile_manager.getAllProfiles():
                if prof.isLocked() is False:
                    profile = prof
                    break

        if profile is None:
            profile = self._profile_manager.addProfile("")
            profile.password = ""

        login.switch_to_profile(profile)

        splash.hide()
        self._main.setTitle("aMSN 2 - Login")
        login.show()

        menu = self.createMainMenuView()
        self._main.setMenu(menu)

    def getMainWindow(self):
        return self._main

    def addProfile(self, account):
        return self._profile_manager.addProfile(account)

    def signinToAccount(self, login_window, profile):
        print "Signing in to account '%s'" % (profile.email)
        profile.login = login_window
        profile.client = protocol.Client(self, profile)
        self._profile = profile
        profile.client.connect()

    def connectionStateChanged(self, profile, state):

        status_str = \
        {
            papyon.event.ClientState.CONNECTING : 'Connecting to server...',
            papyon.event.ClientState.CONNECTED : 'Connected',
            papyon.event.ClientState.AUTHENTICATING : 'Authenticating...',
            papyon.event.ClientState.AUTHENTICATED : 'Password accepted',
            papyon.event.ClientState.SYNCHRONIZING : 'Please wait while your contact list\nis being downloaded...',
            papyon.event.ClientState.SYNCHRONIZED : 'Contact list downloaded successfully.\nHappy Chatting'
        }

        if state in status_str:
            profile.login.onConnecting((state + 1)/ 7., status_str[state])
        elif state == papyon.event.ClientState.OPEN:
            clwin = self._gui.gui.aMSNContactListWindow(self, self._main)
            clwin.profile = profile
            profile.clwin = clwin
            profile.login.hide()
            self._main.setTitle("aMSN 2")
            profile.clwin.show()
            profile.login = None

            self._personalinfo_manager.set_profile(profile)
            self._contactlist_manager.onCLDownloaded(profile.client.address_book)

    def idlerAdd(self, func):
        self._loop.idlerAdd(func)

    def timerAdd(self, delay, func):
        self._loop.timerAdd(delay, func)

    def quit(self):
        self._loop.quit()

    def createMainMenuView(self):
        menu = MenuView()
        quitMenuItem = MenuItemView(MenuItemView.COMMAND, label="Quit", command
                                    = self.quit)
        mainMenu = MenuItemView(MenuItemView.CASCADE_MENU, label="Main")
        mainMenu.addItem(quitMenuItem)

        menu.addItem(mainMenu)

        return menu
