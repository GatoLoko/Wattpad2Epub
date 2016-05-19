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

import sys
import os
import argparse
import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup
import socket
from ebooklib import epub
import re
from string import Template

debug = False

# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)


# Get the page url we want to process
# initial_url = sys.argv[1]
if len(sys.argv) > 1:
    initial_url = sys.argv[1]
else:
    print("You must provide a story URL")
    quit(os.EX_USAGE)

# Sample book URL: http://www.wattpad.com/story/12345678-title-here
# Sample first page URL: http://www.wattpad.com/91011121-title-here

# The following URL's are for testing purposes, overriding address provided
# from command line.
# initial_url = 'http://www.wattpad.com/story/11561902-rainbow-reflection'
# initial_url = 'http://www.wattpad.com/story/27198468-sholan-alliance-bk-3'


def get_html(url):
    tries = 5
    while tries > 0:
        try:
            req = urllib.request.Request(url)
            req.add_header('User-agent', 'Mozilla/5.0 (Linux x86_64)')
            request = urllib.request.urlopen(req)
            # html.parser generates problems, I could fix them, but switching to
            # lxml is easier and faster
            soup = BeautifulSoup(request.read(), "lxml")
            return soup
        except socket.timeout:
            tries -= 1


def clean_text(text):
    text = re.sub(r'<p data-p-id=".{32}">', '<p>', text)
    # text = re.sub(r'&nbsp;', '', text)
    text = re.sub(r'\xa0', '', text)
    return text


def get_page(text_url):
    text = get_html(text_url).select('pre')
    return text


def get_chapter(url):
    pagehtml = get_html(url)
    print("Current url: " + url)
    pages_re = re.compile('"pages":([0-9]*),', re.IGNORECASE)
    pages = int(pages_re.search(str(pagehtml)).group(1))
    print("Pages in this chapter: {}".format(pages))
    text = []
    chaptertitle = pagehtml.select('h2')[0].get_text().strip()
    chapterfile = "{}.xhtml".format(chaptertitle.replace(" ", "-"))
    for i in range(1, pages+1):
        page_url = url + "/page/" + str(i)
        print("Working on: " + page_url)
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

    print("'{}' by {}".format(title, author))
    # print(next_page_url)

    # Get list of chapters
    chapterlist_url = "{}{}".format(initial_url, "/parts")
    chapterlist = get_html(chapterlist_url).select('ul.table-of-contents a')

    epubfile = "{} - {}.epub".format(title, author)
    if not os.path.exists(epubfile):
        book = epub.EpubBook()
        book.set_title(title)
        book.add_author(author)
        book.set_language('en')
        # book.add_metadata('DC', 'subject', 'Wattpad')
        for label in labels:
            book.add_metadata('DC', 'subject', label)
        # TODO: add a cover without breaking everything
        # urllib.request.urlretrieve(coverurl, "cover.jpg")
        # img = open("cover.jpg", "r", encoding="utf-8")
        # book.set_cover('cover.jpg', img)
        # os.remove("cover.jpg")

        # Define CSS style
        nav_css = epub.EpubItem(uid="style_nav", file_name="Style/nav.css",
                                media_type="text/css",
                                content=open("CSS/nav.css").read())

        body_css = epub.EpubItem(uid="style_body", file_name="Style/body.css",
                                 media_type="text/css",
                                 content=open("CSS/body.css").read())
        # Add CSS file
        book.add_item(nav_css)
        book.add_item(body_css)

        # Introduction
        intro_ch = epub.EpubHtml(title='Introduction', file_name='intro.xhtml')
        intro_ch.add_item(body_css)
        intro_template = Template(open("HTML/intro.xhtml").read())
        intro_html = intro_template.substitute(title=title, author=author,
                                               url=initial_url,
                                               synopsis=description)
        intro_ch.content = intro_html
        book.add_item(intro_ch)

        allchapters = []
        for item in chapterlist:
            chaptertitle = item.get_text().strip().replace("/", "-")
            if chaptertitle.upper() != "A-N":
                print("Working on: {}".format(chaptertitle))
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
        myspine = [intro_ch, 'nav']
        for i in allchapters:
            myspine.append(i)
        book.spine = myspine

        # Write the epub to file
        epub.write_epub(epubfile, book, {})
    else:
        print("Epub file already exists, not updating")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download stories from wattpad.com and store them as epub.",
        epilog="This script doesn't support updating an existing epub with " +
               "new chapters",
        argument_default=argparse.SUPPRESS)

    parser.add_argument('initial_url', metavar='initial_url', type=str, nargs=1,
                        help="Book's URL.")
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='print debug messages to stdout')

    args = parser.parse_args()
    if args.debug:
        debug = True
        print(args)

    get_book(args.initial_url[0])