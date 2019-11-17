============
Introduction
============

Getting Started
###############

API Coverage
************

 - `Spotify HTTP REST API`
 - `Spotify Connect Web API`

Concepts
********

Writing a Query - Guidelines
============================

Keyword matching
----------------

Matching of search keywords is not case-sensitive. Operators, however, should
be specified in uppercase. Unless surrounded by double quotation marks,
keywords are matched in any order.

For example: q=roadhouse&20blues matches both “Blues Roadhouse” and “Roadhouse of the Blues”. q="roadhouse&20blues" matches “My Roadhouse Blues” but not “Roadhouse of the Blues”.

Searching
---------

Searching for playlists returns results where the query keyword(s) match any part of the playlist’s name or description. Only popular public playlists are returned.

Operators
---------

.. note::

    Operators must be specified in uppercase. Otherwise, they are handled as normal keywords to be matched.

The operator `NOT` can be used to exclude results.

For example: `q="roadhouse NOT blues"` returns items that match “roadhouse” but excludes those that also contain the keyword “blues”.

Similarly, the `OR` operator can be used to broaden the search: `q="roadhouse OR blues"` returns all the results that include either of the terms. Only one `OR` operator can be used in a query.

Wildcards
---------

The asterisk (*) character can, with some limitations, be used as a wildcard
(maximum: 2 per query). It matches a variable number of non-white-space
characters.

It cannot be used:
 - in a quoted phrase
 - in a field filter
 - when there is a dash (“-“) in the query
 - or as the first character of the keyword string Field filters: By default, results are returned when a match is found in any field of the target object type. Searches can be made more specific by specifying an album, artist or track field filter.

For example: The query q=album:gold%20artist:abba&type=album returns only albums with the text “gold” in the album name and the text “abba” in the artist name.

To limit the results to a particular year, use the field filter year with album, artist, and track searches.

For example: q=bob%20year:2014

Or with a date range. For example: q=bob%20year:1980-2020

To retrieve only albums released in the last two weeks, use the field filter tag:new in album searches.

To retrieve only albums with the lowest 10% popularity, use the field filter tag:hipster in album searches. Note: This field filter only works with album searches.

Depending on object types being searched for, other field filters, include genre (applicable to tracks and artists), upc, and isrc. For example: q=lil%20genre:%22southern%20hip%20hop%22&type=artist. Use double quotation marks around the genre keyword string if it contains spaces.
