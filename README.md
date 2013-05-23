Parse Buyer's Guides (for great justice!)
========================================

There are a lot of consumer campaigns out there on the Internet. Consumer
campaigns supported by perfectly lovely organizations, organized around
causes you wholeheartedly support, that would change the world if enough
people followed through on them.

The [Buycott App](http://www.buycott.com) came out since I started this project,
and it's a step in the right direction: people can create their own Boycott/Buycott
campaigns, and you can use them to inform your buying decisions by scanning barcodes
in the store. This is better than a single campaign app like the [HRC Buyer's Guide on
iPhone](https://itunes.apple.com/us/app/hrc-foundation-buying-for/id345618414?mt=8) or
the [UNITE HERE Hotels Guide](https://itunes.apple.com/us/app/hotels-guide/id557229771?mt=8), but it's still limited to a single use case (scanning barcodes). If you want to
integrate any of the above campaigns into your amazon.com buying decisions, about the best
you can do is open each of their websites in a separate tab.

Really, what we need here is a separation of applications and data. The people who
take the time to put together comprehensive, well-researched buying guides don't have the
time or the resources to write apps. And the people who are good at writing apps probably
don't have the time to sort through all that data.

The end-goal of this project is to create an API for buyer's guides, so that every
buyer's guide out there can be available on any app.

The first major step is to define a [microdata](http://en.wikipedia.org/wiki/Microdata_(HTML)) format for buyer's guides. Microdata's primary use case is annotating web pages in
a machine readable way, which means that if you want a buyer's guide to be added to
the API, all you have to do is write HTML. Microdata also has a little-known [standard
JSON format](http://www.whatwg.org/specs/web-apps/current-work/multipage/microdata.html#json), which is great for an API, and for a JSON datastore such as [CouchDB](http://couchdb.apache.org/).

To ensure that the format reflects real use cases, we're going to parse real buyer's guides
available on the web, that target a variety of things (corporations, local businesses,
types of fish). These parsers could also be used to seed a new API with useful data, though if the buzz around the Buycott App is any indication, seeding won't really be
an issue.

So having everything in the same format would certainly be convenient, but what else could
we do with a buyer's guide API?

* Browser plugins. Amazon.com plugins would probably have the most economic impact, but
  you could really annotate any webpage. The [ThinkContext plugin](http://thinkcontext.org/)
  is pretty useful, and it only supports a handful of buyer's guides.
* Automatically convert lobbying/campaign contribution data into consumer campaigns, using
  [opensecrets.org] or something similar. Support a bill? Boycott the companies trying to
  squash it. Oppose a bill? Boycott the companies behind it.
* Work our way up the supply chain. If you have a problem with a company like [Cargill](http://www.cargill.com/), which mostly sells to businesses, consumer actions aren't going to have much affect (if it makes you feel better, you can boycott Truvia). However, if we have a way for local businesses to publicly advertise that they subscribe to a particular campaign (e.g. not using Cargill products in their restaurant), then consumers can support those businesses.
* Apps that work on Android without a network connection. Not really so much to ask.
* Stuff that no one has imagined yet. Give people the tools, and someone will do something amazing.

How to Help
===========

Finding Buying Guides
---------------------

I need your help finding interesting guides with useful data. If you use
GitHub, submit pull requests for changes to `TODO.txt`. If you don't, just
email me at <dm@davidmarin.org>.

Criteria for guides:
* Choose guides on sites that allow or do not explicitly ban downloading their
content and redistributing it (look at the Terms of Use, and, if you know how
to read it, [`robots.txt`](http://en.wikipedia.org/wiki/Robots_exclusion_standard)).
  * Few sites explicitly allow redistributing their content ([here is one](http://www.edf.org/about/this-site/copyright)), but that's fine. I'm going off the maxim that [it's easier to ask forgiveness than to get permission](http://en.wikiquote.org/wiki/Grace_Hopper). Most of these organizations are just trying to
make the world a better place, and if we can help spread the word without
screwing up their data, probably everyone will be happy.
* Try to expose corner cases early:
  * Include a variety of targets (companies, brands, products, foods)
  * Aim for some overlap between guides, especially conflicting recommendations
* Prefer campaigns that have a decent-sized following and are based on
  accurate information.
* Avoid campaigns that have not been updated for more than a year.
* Simple campaigns targeting a single company or product are A-OK.

Writing parsers
---------------

I've started writing parsers in Python. The [parser for the HRC buyer's guide](https://github.com/davidmarin/pbg/blob/master/python/pbg/hrc/buyersguide/data.py)
is probably the best example so far, both in terms of structure and the format
of the data it outputs.

Parsing web pages is not rocket science; it's barely computer science. If
you're new to programming, or have used Python a few times but don't consider
yourself a programmer, you can do this, there are good libraries, and I'll help
you out. And of course, if you're a good programmer, this should be a snap;
why not help out and get your name on an Open Source project? :)

My goal for Python code is that it be [version agnostic](http://python3porting.com/noconv.html), but if you don't know what this means or how to do it, that's
OK. Other languages are fine too; just make a new subdirectory for the language
of your choice.

Other guidelines:
* Accuracy above all else; parsers should fail fast (crash) in the presence of
  unexpected changes rather than producing bad or incomplete data.
  (In Python, use `pyassert`).
* Include as much data as possible. Exceptions:
  * Try to avoid needing to download one page per product.
  * Don't scrape the long-form description of the campaign; try to grab
    a one-or-two paragraph summary and include URLs for the rest.
  * Output text, not HTML.
* Try to make scripts that just process data, and leave network access to
  other processes (e.g. curl).
  * See the top of [pbg.hrc.buyersguide.data](https://github.com/davidmarin/pbg/blob/master/python/pbg/hrc/buyersguide/data.py) for an example two-step process
    that processes multiple pages on one site. If you are recursively scraping
    a website to an unknown depth, you are probably off track.
* Write unit tests for shared/general code, but don't worry about testing
  individual parsers. They will be continuously integration-tested anyway.
