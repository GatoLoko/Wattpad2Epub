# -*- coding: utf-8 -*-
"""
====
Custom networking functions
====

Mostly customized http request for now
"""

# import brotli
import gzip
from io import BytesIO
import platform
import socket
import urllib.request
import urllib.parse
import urllib.error

from bs4 import BeautifulSoup


# set timeout to 10 seconds
socket.setdefaulttimeout(10)

# Create our own User-Agent string. We may need to fake this if a server tryes
# to mess with us.
USER_AGENT = 'Mozilla/5.0 compatible (' + platform.system() + ' ' + \
    platform.machine() + '; Novel-Indexer-Bot)'


# Provide a function to replace the default User-Agent:
def set_user_agent(agent):
    global USER_AGENT
    USER_AGENT = agent


def get_url(url):
    tryes = 5
    response = None
    # Build our request
    request = urllib.request.Request(url)
    # Accept compressed content
    request.add_header('Accepting-encoding', 'gzip, br')
    # Use our custom User-Agent
    request.add_header('User-Agent', USER_AGENT)
    # Add DoNotTrack header, do the right thing even if nobody cares
    request.add_header('DNT', '1')

    while tryes > 0:
        try:
            response = urllib.request.urlopen(request)
            break
        except socket.timeout:
            tryes -= 1
        except urllib.error.URLError as error:
            if isinstance(error.reason, socket.timeout):
                tryes -= 1
            else:
                raise SystemExit("An URL error happened: -%s-" % error.reason)\
                    from error

    encoding = response.info().get('Content-Encoding')
    if encoding == 'gzip':
        buffer = BytesIO(response.read())
        content = gzip.GzipFile(fileobj=buffer)
    elif encoding == 'br':
        # content = brotli.decompress(response.content)
        content = response.text
        print("Brotli: " + content)
    else:
        content = response.read()
    response.close()
    return content


def get_soup(url):
    html = get_url(url)
    soup = BeautifulSoup(html, 'lxml')
    return soup
