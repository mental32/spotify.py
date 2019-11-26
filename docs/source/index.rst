Welcome to spotify.py's documentation!
======================================

.. image:: /_static/images/logo.png

What is `spotify.py`?
---------------------

Spotify.py is a modern, friendly, and Pythonic API library for the Spotify API.

Quick example
~~~~~~~~~~~~~

This example shows effectively using the library to iterate over an albums tracks.

.. code-block:: py

    import asyncio

    import spotify

    ALBUM_URI: str = "foo bar baz"
    CLIENT_ID: str = "lorem ipsum"
    CLIENT_SECRET: str = "dolor sit amet"

    async def main(ident: str, secret: str, album_uri: str) -> None:
        # Useful tip: use a context manager to handle
        # automatically closing any underlying http sessions
        async with spotify.Client(ident, secret) as client:
            album = await client.get_album(album_uri)

            async for track in album:
                print(repr(track))

    asyncio.run(main(CLIENT_ID, CLIENT_SECRET, ALBUM_URI))

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   introduction
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
