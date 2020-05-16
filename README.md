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
`python3 wattpad2epub.py your_url_argument`. If it doesn't work, try to use `python wattpad2epub.py your_url_argument`

> `your_url_argument` should be your story url, for example: `http://www.wattpad.com/story/53207033-the-arwain-chronicles`

## Output

After the script finished, you will have your epub file inside the root folder, and
it will be named in the format `Title - Author .epub`, for example:
`The Arwain Chronicles Book I - IceheartPhoenix.epub`

## On Wattpad's API

As of Dec. 2018m the API has been split into two part, a "public API" and a
"private API".

[Public API](https://www.wattpad.com/developer/docs/api):

  - Has been in beta state since 2015, and they warn that it's subject to
    change, which makes it unreliable. (2018)
  - Does NOT provide a way to retrieve story or chapter text, making it
    unsuitable for Wattpad2Epub purposes. (2018)
  - Needs double authentication (application + user). (2015-2018)

[Private API](http://developer.wattpad.com/docs/api):

  - Has been moved behind a login for which the wattpad user account doesnt
    work and there is nothing to help you find out how to gain access or
    whether it's at all possible. (2018)
  - Isn't publicized. Found it through a
    [comment on Stack Overflow](https://stackoverflow.com/questions/27070973/does-wattpad-have-an-api),
    which probably means it's not meant for external applications use. (2018)
  - When the documentation for the "private API" was accesible it was
    incomplete, with some essential parts missing. (2015)
  - There were some server failures during my tests. (2015)
  - Couldn't find a reliable way to retrieve a full story text. (2015)
  - Needs double authentication (application + user). (2015-2018)

Based on all this, I've given up on using the API at all, and chosen to keep
parsing the html because it allows us to:

  - Retrieve full story text (essential)
  - Not require the user to authenticate (important)
  - Not require application autentication (nice to have)

