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
from bs4 import BeautifulSoup
import socket
from ebooklib import epub, VERSION
import re
from string import Template

debug = False

chapterCount = 0                
# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

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
    req = urllib.request.Request(url)
    req.add_header('User-agent', 'Mozilla/5.0 (Linux x86_64)')
    # Add DoNotTrack header, do the right thing even if nobody cares
    req.add_header('DNT', '1')
    while tries > 0:
        try:
            request = urllib.request.urlopen(req)
            tries = 0
        except socket.timeout:
            if debug:
                raise
            tries -= 1
        except socket.timeout:
            if debug:
                raise
            tries -= 1
        except urllib.error.URLError as e:
            if debug:
                raise
            print("URL Error " + str(e.code) + ": " + e.reason)
            print("Aborting...")
            exit()
        except urllib.error.HTTPError as e:
            if debug:
                raise
            print("HTTP Error " + str(e.code) + ": " + e.reason)
            print("Aborting...")
            exit()
    # html.parser generates problems, I could fix them, but switching to lxml
    # is easier and faster
    soup = BeautifulSoup(request.read(), "lxml")
    return soup


def get_cover(cover_url):
    print(cover_url)
    tries = 5
    while tries > 0:
        try:
            req = urllib.request.Request(cover_url)
            req.add_header('User-agent', 'Mozilla/5.0 (Linux x86_64)')
            request = urllib.request.urlopen(req)
            temp = request.read()
            with open('cover.jpg', 'wb') as f:
                f.write(temp)
            tries == 0
            # break
            return 1
        except Exception as error:
            tries -= 1
            print("Can't retrieve the cover")
            print(error)
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
    text = get_html(text_url).select('pre')
    return text


def get_chapter(url):
    global chapterCount
    chapterCount = chapterCount + 1
    pagehtml = get_html(url)
    print("Current url: " + url)
    pages_re = re.compile('"pages":([0-9]*),', re.IGNORECASE)
    pages = int(pages_re.search(str(pagehtml)).group(1))
    print("Pages in this chapter: {}".format(pages))
    text = []
    chaptertitle = pagehtml.select('h2')[0].get_text().strip()
    chapterfile = "{}.xhtml".format(chaptertitle.replace(" ", "-") + "-" + str(chapterCount))
    text.append("<h2>{}</h2>\n".format(chaptertitle))
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
    if debug:
        print("Author: " + author)
        print("Title: " + title)
        print("Description: " + description)
        print("Cover: " + coverurl)
        print("Labels:" + " ".join(labels))

    print("'{}' by {}".format(title, author).encode("utf-8"))
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
        css_path = os.path.join("CSS", "nav.css")
        nav_css = epub.EpubItem(uid="style_nav", file_name="Style/nav.css",
                                media_type="text/css",
                                content=open(css_path).read())

        css_path = os.path.join("CSS", "body.css")
        body_css = epub.EpubItem(uid="style_body", file_name="Style/body.css",
                                 media_type="text/css",
                                 content=open(css_path).read())
        # Add CSS file
        book.add_item(nav_css)
        book.add_item(body_css)

        # Introduction
        intro_ch = epub.EpubHtml(title='Introduction', file_name='intro.xhtml')
        intro_ch.add_item(body_css)
        template_path = os.path.join("HTML", "intro.xhtml")
        intro_template = Template(open(template_path).read())
        intro_html = intro_template.substitute(title=title, author=author,
                                               url=initial_url,
                                               synopsis=description)
        intro_ch.content = intro_html
        book.add_item(intro_ch)

        allchapters = []
        for item in chapterlist:
            chaptertitle = item.get_text().strip().replace("/", "-")
            if chaptertitle.upper() != "A-N":
                print("Working on: {}".format(chaptertitle).encode("utf-8"))
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
    else:
        print("Epub file already exists, not updating")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download stories from wattpad.com and store them as"
                    " epub.",
        epilog="This script doesn't support updating an existing epub with new"
               " chapters",
        argument_default=argparse.SUPPRESS)

    parser.add_argument('initial_url', metavar='initial_url', type=str,
                        nargs=1, help="Book's URL.")
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='print debug messages to stdout')

    args = parser.parse_args()
    if args.debug:
        debug = True
        print(args)

    get_book(args.initial_url[0])
