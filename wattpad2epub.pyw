#!/usr/bin/env python3

# Copyright (C) 2015 GatoLoko
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
Created on Wed Feb 18 22:26:23 2015

@author: gatoloko
"""

import os
import argparse
import urllib.request
import urllib.parse
import urllib.error
from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showinfo, showerror
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup
import socket
from ebooklib import epub, VERSION
import re
from string import Template

chapterCount = 0                
# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

if os.path.islink(__file__):
    mypath = os.path.dirname(os.path.realpath(__file__))
else:
    mypath = os.path.dirname(os.path.abspath(__file__))
# print(mypath)


# Sample book URL: http://www.wattpad.com/story/12345678-title-here
# Sample first page URL: http://www.wattpad.com/91011121-title-here

# The following URL's are for testing purposes. All of them have unique
# situations that make them worth testing (e.g. "The Arwain chronicles" book
# has some weirdly formated chapters that make wattpad's android app choke
# and take forever loading them)

# Since the change in arguments parsing, uncommenting this lines has no
# effect, and remain here as a reminder.
# initial_url = 'http://www.wattpad.com/story/53207033-the-arwain-chronicles'
# initial_url = 'http://www.wattpad.com/story/11561902-rainbow-reflection'
# initial_url = 'http://www.wattpad.com/story/27198468-sholan-alliance-bk-3'


def get_html(url):
    tries = 5
    try:
        req = urllib.request.Request(url)
    except ValueError:
        showerror("Error", "Invalid URL: " + url)
        return
    req.add_header('User-agent', 'Mozilla/5.0 (Linux x86_64)')
    # Add DoNotTrack header, do the right thing even if nobody cares
    req.add_header('DNT', '1')
    while tries > 0:
        try:
            request = urllib.request.urlopen(req)
            tries = 0
        except socket.timeout:
            tries -= 1
            tries -= 1
        except urllib.error.URLError as e:
            showerror("Url Error", str(e) + ": " + e.reason + "\nAborting...")
            return
        except urllib.error.HTTPError as e:
            showerror("HTTP Error ", str(e.code) + ": " + e.reason + "\nAborting...")
            return
    # html.parser generates problems, I could fix them, but switching to lxml
    # is easier and faster
    soup = BeautifulSoup(request.read(), "lxml")
    return soup


def get_cover(cover_url):
    tries = 5
    while tries > 0:
        try:
            try:
                req = urllib.request.Request(cover_url)
            except ValueError:
                showerror("Error", "Invalid URL: " + cover_url)
                return
            req.add_header('User-agent', 'Mozilla/5.0 (Linux x86_64)')
            request = urllib.request.urlopen(req)
            temp = request.read()
            with open('cover.jpg', 'wb') as f:
                f.write(temp)
            # break
            return 1
        except Exception as error:
            tries -= 1
            showerror("Error", "Can't retrieve the cover:\n" + str(error))
            return 0


###############################################################################
# TODO: Remove this block when appropriate
# Workaround for bug in ebooklib 0.15.
# Something goes wrong when adding an image as a cover, and we need to work
# around it by replacing the get_template function with our own that takes care
# of properly encoding the template as utf8.
if VERSION[1] == 15:
    original_get_template = epub.EpubBook.get_template

    def new_get_template(*args, **kwargs):
        return original_get_template(*args, **kwargs).encode(encoding='utf8')

    epub.EpubBook.get_template = new_get_template
###############################################################################


def clean_text(text):
    text = re.sub(r'<p data-p-id=".{32}">', '<p>', text)
    # text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'\xa0', '', text)
    return text


def get_page(text_url):
    text = get_html(text_url).select_one('pre').findChildren()
    return text


def get_chapter(url):
    global chapterCount
    chapterCount = chapterCount + 1
    pagehtml = get_html(url)
    pages_re = re.compile('"pages":([0-9]*),', re.IGNORECASE)
    pages = int(pages_re.search(str(pagehtml)).group(1))
    text = []
    chaptertitle = pagehtml.select('h2')[0].get_text().strip()
    chapterfile = "{}.xhtml".format(chaptertitle.replace(" ", "-") + "-" + str(chapterCount))
    text.append("<h2>{}</h2>\n".format(chaptertitle))
    for i in range(1, pages+1):
        page_url = url + "/page/" + str(i)
        text.append('<div class="page">\n')
        for j in get_page(page_url):
            text.append(j.prettify())
        text.append('</div>\n')
    chapter = epub.EpubHtml(title=chaptertitle, file_name=chapterfile,
                            lang='en')
    chapter.content = "".join(text)
    return chapter


def get_book(initial_url):
    base_url = 'http://www.wattpad.com'
    html = get_html(initial_url)

    # Get basic book information
    author = html.select('div.author-info strong a')[0].get_text()
    title = html.select('h1')[0].get_text().strip()
    description = html.select('h2.description')[0].get_text()
    coverurl = html.select('div.cover.cover-lg img')[0]['src']
    labels = ['Wattpad']
    for label in html.select('div.tags a'):
        if '/' in label['href']:
            labels.append(label.get_text())

    # print(next_page_url)

    # Get list of chapters
    chapterlist_url = "{}{}".format(initial_url, "/parts")
    chapterlist = get_html(chapterlist_url).select('ul.table-of-contents a')

    # Remove from the file name those characters that Microsoft does NOT allow.
    # This also affects the FAT filesystem used on most phone/tablet sdcards
    # and other devices used to read epub files.
    # Disallowed characters: \/:*?"<>|^
    filename = title
    for i in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '^']:
        if i in filename:
            filename = filename.replace(i, '')
    # Apple products disallow files starting with dot
    filename = filename.lstrip('.')

    epubfile = "{} - {}.epub".format(filename, author)
    if not os.path.exists(epubfile):
        book = epub.EpubBook()
        book.set_identifier("wattpad.com//%s/%s" % (initial_url.split('/')[-1],
                                                    len(chapterlist)))
        book.set_title(title)
        book.add_author(author)
        book.set_language('en')
        # book.add_metadata('DC', 'subject', 'Wattpad')
        for label in labels:
            book.add_metadata('DC', 'subject', label)
        # Add a cover if it's available
        if get_cover(coverurl):
            cover = True
            book.set_cover(file_name='cover.jpg', content=open('cover.jpg',
                                                               'rb').read(),
                           create_page=True)
            os.remove('cover.jpg')

        # Define CSS style
        css_path = os.path.join(mypath, "CSS", "nav.css")
        nav_css = epub.EpubItem(uid="style_nav", file_name="Style/nav.css",
                                media_type="text/css",
                                content=open(css_path).read())

        css_path = os.path.join(mypath, "CSS", "body.css")
        body_css = epub.EpubItem(uid="style_body", file_name="Style/body.css",
                                 media_type="text/css",
                                 content=open(css_path).read())
        # Add CSS file
        book.add_item(nav_css)
        book.add_item(body_css)

        # Introduction
        intro_ch = epub.EpubHtml(title='Introduction', file_name='intro.xhtml')
        intro_ch.add_item(body_css)
        template_path = os.path.join(mypath, "HTML", "intro.xhtml")
        intro_template = Template(open(template_path).read())
        intro_html = intro_template.substitute(title=title, author=author,
                                               url=initial_url,
                                               synopsis=description)
        intro_ch.content = intro_html
        book.add_item(intro_ch)

        allchapters = []
        progress_increments = 100/len(chapterlist)
        for item in chapterlist:
            chaptertitle = item.get_text().strip().replace("/", "-")
            if chaptertitle.upper() != "A-N":
                progress["value"] += progress_increments
                chapter = get_chapter("{}{}".format(base_url, item['href']))
                book.add_item(chapter)
                allchapters.append(chapter)

        # Define Table of Contents
        book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                    (epub.Section('Chapters'), allchapters))

        # Add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Basic spine
        myspine = []
        if cover:
            myspine.append('cover')
        myspine.extend([intro_ch, 'nav'])
        myspine.extend(allchapters)
        book.spine = myspine

        # Write the epub to file
        epub.write_epub(epubfile, book, {})

        # Show done
        showinfo("Completed", "Book \"{}\" finished downloading.".format(title))
    else:
        showerror("Already Exists", "Epub file already exists, not updating")


if __name__ == "__main__":
    thread = None

    def start_download():
        global thread
        thread = Thread(target=lambda: get_book(url_entry.get()))
        thread.daemon = True
        submit_button.config(state=DISABLED)
        thread.start()
        root.after(15, check_thread)

    def check_thread():
        global thread
        if thread is None:
            return
        elif thread.is_alive():
            root.after(15, check_thread)
        else:
            submit_button.config(state=NORMAL)
            progress["value"] = 0
            thread = None

    root = Tk()
    root.title("Wattpad2Epub")
    root.resizable(0,0)
    url_entry = ttk.Entry(root, width=50)
    submit_button = ttk.Button(root, text="Submit", command=start_download)
    progress = ttk.Progressbar(root, orient=HORIZONTAL, mode="determinate")
    url_entry.grid(row=0, column=0, columnspan=3, sticky="we", padx="10", pady="3")
    progress.grid(row=1, column=0, columnspan=3, sticky="we", padx="10", pady="3")
    submit_button.grid(row=2, column=1)

    root.mainloop()
