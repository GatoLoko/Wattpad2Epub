# Readme

## What is Wattpad2Epub

Wattpad2Epub downloads and converts Wattpad books into Epub files you can use
with your favorite ebook reader.

## Why Wattpad2Epub?

Wattpad doesn't offer an option to download a book. This forces you to remain
online while reading, and use wattpad's application to access the stories.

Having those stories in epub format allows storing them as a backup, offline
reading and self publication.

## Requeriments

You will need python3. You can install it with brew in osx.
For our main script you will need BeatifulSoup4 and ebooklib,
you can install them with:
```
pip3 install BeautifulSoup4
pip3 install ebooklib
```

## Running it

You can run the python script doing:
`python3 wattpad2epub.py your_url_argument`

> `your_url_argument` should be your story url, for example: `http://www.wattpad.com/story/53207033-the-arwain-chronicles`

## Output

After the script finished, you will have your epub file inside the root folder, and
it will be named in the format `Title - Author .epub`, for example:
`The Arwain Chronicles Book I - IceheartPhoenix.epub`

## On Wattpad's API

I've made some quick & dirty tests using the official Wattpad API, and most
probably made a few mistakes, but here is what I've found:

  - It's in beta state, wich means it may still change
  - The documentation seems to be missing some parts
  - There were some server failures during my tests
  - Couldn't find a reliable way to retrieve a full story text
  - Needed double authentication (application + user)

Based on this findings, I've chosen to keep parsing the html, at least for a
now, for the following reasons:

  - Ability to retrieve full story text (essential)
  - No user authentication needed (important)
  - No application autentication

If you can figure out a way to do this using [Wattpad's
api](https://developer.wattpad.com/docs/api), I'm open to suggestions and/or
patches.
