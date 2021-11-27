#!/usr/bin/env python3

# Copyright (C) 2019 Joeri-G
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""
Created on 27-11-2021

@author: Joeri-G

===
Basic GUI implementation with easygui
https://easygui.readthedocs.io/en/latest/
===
"""
import threading, sys
try:
    import easygui
except ImportError:
    raise

VERSION = '1.0'

class GUI(object):

    STANDARD_TITLE = "Wattpad Downloader [v%s]" % VERSION
    STANDARD_LOCATION = "%USERPROFILE%\\Documents" if sys.platform == "win32" else "~/Documents"

    def __init__(self):
        super(GUI, self).__init__()
        self.download_function = lambda url, location: print("Download function has not been attatched")


    def initialize_GUI(self):
        self.mode_selection_screen()

    def mode_selection_screen(self):
        # check how many eboos the user wants to download
        choice_ist = ('Single Story Download', 'Bulk Download')
        choice = easygui.choicebox(msg="Welcome to Wattpad Downloader",
                          title=self.STANDARD_TITLE,
                          choices=choice_ist,
                          preselect=0)

        for i, item in enumerate(choice_ist):
            if item == choice:
                self.download_select(i)
                break

        # easygui.textbox(msg='Wattpad URLs\n 1 URL per line', title='Wattpad Downloader')
    def download_select(self, type):
        if type == 0: # standard 1 book download
            self.single_book_donwload()
        elif type == 1:
            self.bulk_download()
        else:
            easygui.msgbox("This option has not been implemented yet")

    def single_book_donwload(self):
        url = easygui.enterbox(msg="Whattpad Book URL & Save Location",
                               title=self.STANDARD_TITLE,
                               default="http://www.wattpad.com/story/12345678-title-here")
        savelocation = easygui.diropenbox(msg="Save location",
                                          title=self.STANDARD_TITLE,
                                          default=self.STANDARD_LOCATION)
        if savelocation == None:
            easygui.msgbox(msg="A savelocation is required", title=self.STANDARD_TITLE)
            return
        try:
            if easygui.ynbox(msg="Download [%s]?" % url, title=self.STANDARD_TITLE):
                self.download_function(url, savelocation)
                easygui.msgbox(msg="Download Finnished.\nFile saved to [%s]" % savelocation,
                               title=self.STANDARD_TITLE)
            else:
                easygui.msgbox(msg="Download Aborted", title=self.STANDARD_TITLE)
        except Exception as e:
            errmsg = "It looks like something went wrong... Your download failed.\n\n%s" % str(e)
            easygui.msgbox(msg=errmsg, title=self.STANDARD_TITLE)

    def bulk_download(self):
        user_input = easygui.textbox(msg = "Please enter one URL per line",
                                   title=self.STANDARD_TITLE,
                                   text="http://www.wattpad.com/story/12345678-title-here")
        url_list = user_input.split("\n")
        savelocation = easygui.diropenbox(msg="Save location",
                                          title=self.STANDARD_TITLE,
                                          default=self.STANDARD_LOCATION)
        if savelocation == None:
            easygui.msgbox(msg="A savelocation is required", title=self.STANDARD_TITLE)
            return
        for url in url_list:
            # skip if line is empty
            if not url or url.isspace():
                continue
            self.create_threaded_msgbox("Downloading [%s]" % url)
            try:
                print(url)
                self.download_function(url, savelocation)
            except Exception as e:
                errmsg = "It looks like something went wrong... Your download failed.\n\n%s" % str(e)
                easygui.msgbox(msg=errmsg, title=self.STANDARD_TITLE)

        easygui.msgbox(msg="Downloads Finnished.\nFiles saved to [%s]" % savelocation,
                       title=self.STANDARD_TITLE)

    # Create a msgbox on a separate thread so that it will not halt the process
    # Useful when downloading several ebooks in succession
    def create_threaded_msgbox(self, msg):
        # create lambda function to make the creation of the thread less of an issue
        shorthand = lambda text: easygui.msgbox(msg=text, title=self.STANDARD_TITLE)
        thr = threading.Thread(target=shorthand, args=(msg,), daemon=True)
        thr.start()
