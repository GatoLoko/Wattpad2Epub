# Readme

## What is Wattpad2Epub

Wattpad2Epub downloads and converts Wattpad books into Epub files you can use with your favorite ebook reader.

NOTE: Current version has been rendered obsolete by a change on wattpad site. I'll try to fix it using the official wattpad api.

## On Wattpad's API

I've made some quick & dirty tests using the official Wattpad API, and most probably made a few mistakes, but here is what I've found:

  - It's in beta state
  - The documentation seems to be missing some parts
  - There were some server failures during my tests
  - Couldn't find a reliable way to retrieve a full story text
  - Needed double identification (application + user)

Based on this findings, I've chosen to keep parsing the html, at least for a while.

## Why Wattpad2Epub?

Wattpad doesn't offer an option to download a book. This forces you to remain online while reading, and use wattpad's application to access the stories.

Having those stories in epub format allows storing them as a backup, offline reading and self publication.