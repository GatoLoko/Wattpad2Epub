#!/usr/bin/env python3

# Copyright (C) 2019 GatoLoko
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
Created on 5/01/19

@author: GatoLoko
"""

import string
from string import Template
import ebooklib
from ebooklib import epub


# Limit chapter file names to characters that wont cause problems.
VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)

###############################################################################
# TODO: Remove this block when the fix is propagated to most distros
# Something goes wrong when adding an image as a cover, and we need to work
# around it by replacing the get_template function with our own that takes care
# of properly encoding the template as utf8.
# The bug was fixed upstream but debian/ubuntu and others haven't packaged new
# releases of ebooklib since 2014.
# This will become unnecessary once v0.16 enters the repositories
if ebooklib.VERSION < (0, 16, 0):
    original_get_template = epub.EpubBook.get_template

    def new_get_template(*args, **kwargs):
        return original_get_template(*args, **kwargs).encode(encoding='utf8')

    epub.EpubBook.get_template = new_get_template
###############################################################################


class MyBook:
    def __init__(self, identifier, title, language, application):
        self.title = title
        self.application = application
        self.has_cover = False
        self.all_chapters = []
        self.intro_ch = ""
        self.body_css = ""
        self.book = epub.EpubBook()
        self.book.set_identifier(identifier)
        self.book.set_title(self.title)
        self.book.set_language(language)
        self.book.add_metadata('DC', 'subject', self.application)

    def add_author(self, author):
        self.book.add_author(author)

    def add_labels(self, labels):
        for label in labels:
            self.book.add_metadata('DC', 'subject', label)

    def add_cover(self, cover_file):
        with open(cover_file, 'rb') as cover:
            self.book.set_cover(file_name='cover.jpg', content=cover.read(),
                                create_page=True)
        self.has_cover = True

    def add_chapter(self, ch_title, ch_file, ch_lang, ch_text):
        # Replace non ascii hyphens with ascii ones
        ch_file = ch_file.replace('–', '-') + '.xhtml'
        # Remove any remaining non-ascii characters from file name to avoid
        # problems
        ch_file = ''.join(c for c in ch_file if c in VALID_CHARS)
        chapter = epub.EpubHtml(title=ch_title, file_name=ch_file,
                                lang=ch_lang)
        chapter.content = ch_text
        self.book.add_item(chapter)
        self.all_chapters.append(chapter)

    def add_nav_style(self, css):
        # Define the CSS style
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css",
                                media_type="text/css", content=css)
        # Add the style as a file
        self.book.add_item(nav_css)

    def add_body_style(self, css):
        # Define the CSS style
        self.body_css = epub.EpubItem(uid="style_body",
                                      file_name="style/body.css",
                                      media_type="text/css", content=css)
        # Add the style as a file
        self.book.add_item(self.body_css)

    def add_intro(self, author, url, synopsis, template_file):
        self.intro_ch = epub.EpubHtml(title='Introduction',
                                      file_name='intro.xhtml')
        self.intro_ch.add_item(self.body_css)
        with open(template_file) as infile:
            in_template = Template(infile.read())
        self.intro_ch.content = in_template.substitute(title=self.title,
                                                       author=author,
                                                       url=url,
                                                       synopsis=synopsis)
        self.book.add_item(self.intro_ch)

    def finalize(self):
        # Define Table of Content
        self.book.toc = (epub.Link('intro.xhtml', 'Introduction', 'intro'),
                         (epub.Section('Chapters'), self.all_chapters))
        # Add default NCX and NAV
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        # Add basic spine
        myspine = []
        if self.has_cover:
            myspine.append('cover')
        myspine.extend([self.intro_ch, 'nav'])
        myspine.extend(self.all_chapters)
        self.book.spine = myspine

    def write(self, filename):
        epub.write_epub(filename, self.book, {})
