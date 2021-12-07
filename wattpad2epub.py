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

import argparse
import os
import sys
import re

PROG_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(PROG_DIR, "libs"))
try:
    import gsweb
    from gsepub import MyBook
    from gui import GUI
except ImportError:
    raise

debug = False

chapterCount = 0

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


def get_cover(cover_url, cover_file):
    print(cover_url)
    try:
        with open(cover_file, 'wb') as f:
            f.write(gsweb.get_url(cover_url))
        return 1
    except Exception as error:
        # print("Can't retrieve the cover")
        # print(error)
        # print("Continuing without a cover")
        raise Exception("Can't retrieve cover", error)
        return 0


def clean_text(text):
    text = re.sub(r'<p data-p-id=".{32}">', '<p>', text)
    # text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'\xa0', '', text)
    return text


def get_page(text_url):
    text = gsweb.get_soup(text_url).select_one('pre').findChildren()
    return text


def get_chapter(url):
    global chapterCount
    chapterCount = chapterCount + 1
    pagehtml = gsweb.get_soup(url)
    print("Current url: " + url)
    pages_re = re.compile('"pages":([0-9]*),', re.IGNORECASE)
    pages = int(pages_re.search(str(pagehtml)).group(1))
    print("Pages in this chapter: {}".format(pages))
    text = []
    chaptertitle = pagehtml.select('h1.h2')[0].get_text().strip()
    chapterfile = "{}.xhtml".format(chaptertitle.replace(" ", "-") + "-" +
                                    str(chapterCount))
    text.append("<h2>{}</h2>\n".format(chaptertitle))
    for i in range(1, pages+1):
        page_url = url + "/page/" + str(i)
        print("Working on: " + page_url)
        text.append('<div class="page">\n')
        for j in get_page(page_url):
            text.append(j.prettify())
        text.append('</div>\n')
    chapter = "".join(text)
    return chaptertitle, chapterfile, chapter


def get_book(initial_url, base_dir):
    base_url = 'http://www.wattpad.com'
    html = gsweb.get_soup(initial_url)

    # Get basic book information
    author = html.select('div.author-info__username')[0].get_text()
    title = html.select('div.story-info__title')[0].get_text().strip()
    description = html.select('pre.description-text')[0].get_text()
    coverurl = html.select('div.story-cover img')[0]['src']
    labels = ['Wattpad']
    for label in html.select('div.tags a'):
        if '/' in label['href']:
            labels.append(label.get_text())
    if debug:
        print("Author: " + author)
        print("Title: " + title)
        print("Description: " + description)
        print("Cover: " + coverurl)
        print("Labels:" + " ".join(labels))

    print("'{}' by {}".format(title, author).encode("utf-8"))
    # print(next_page_url)

    # Get list of chapters
    chapterlist = list(dict.fromkeys(html.select('.story-parts ul li a')))

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

    epubfile = os.path.join(base_dir, "{} - {}.epub".format(filename, author))
    if not os.path.exists(epubfile):
        identifier = "wattpad.com//%s/%s" % (initial_url.split('/')[-1],
                                             len(chapterlist))
        LANGUAGE = 'en'
        book = MyBook(identifier, title, LANGUAGE, 'wattpad2epub')
        book.add_author(author)
        # Add all labels.
        book.add_labels(labels)
        # Add a cover if it's available
        cover_file = 'cover.jpg'
        if get_cover(coverurl, cover_file):
            book.add_cover(cover_file)
            os.remove(cover_file)

        # Define CSS style
        with open(os.path.join(PROG_DIR, "CSS", "nav.css")) as style_nav:
            book.add_nav_style(style_nav.read())
        with open(os.path.join(PROG_DIR, "CSS", "body.css")) as style_body:
            book.add_body_style(style_body.read())

        # Introduction
        book.add_intro(author, initial_url, description,
                       os.path.join(PROG_DIR, "HTML", "intro.xhtml"))

        for item in chapterlist:
            chaptertitle = item.get_text().strip().replace("/", "-")
            if chaptertitle.upper() != "A-N":
                print("Working on: {}".format(chaptertitle))
                ch_title, ch_file, ch_text = get_chapter(
                    "{}{}".format(base_url, item['href']))
                book.add_chapter(chaptertitle, ch_file, LANGUAGE, ch_text)

        # Define Table of Contents, NCX, Nav and book spine
        book.finalize()

        # Write the epub to file
        book.write(epubfile)

    else:
        raise Exception("Epub file already exists, not updating")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download stories from wattpad.com and store them as"
                    " epub.",
        epilog="This script doesn't support updating an existing epub with new"
               " chapters",
        argument_default=argparse.SUPPRESS)

    parser.add_argument('initial_url', metavar='initial_url', type=str,
                        nargs='?', default=[], help="Book's URL.")
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='print debug messages to stdout')

    parser.add_argument('--cli', action='store_true', default=False,
                        help='run in GUI mode')

    args = parser.parse_args()
    if args.debug:
        debug = True
        print(args)

    if len(args.initial_url) == 0 and not args.cli:
        gui = GUI() # start GUI if no URL has been specified
        gui.download_function = get_book
        gui.initialize_GUI()
    elif args.initial_url or args.cli:
        get_book(args.initial_url, mypath)
