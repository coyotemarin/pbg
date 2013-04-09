Parse Buying Guides (for great justice!)
========================================

There are a lot of consumer campaigns out there on the Internet. Consumer
campaigns supported by perfectly lovely organizations, organized around
causes you wholeheartedly support, that would change the world if enough
people followed through on them.

But when it comes time to make purchasing decisions, who can keep track of all
[the brands owned by the Koch Brothers](http://www.boycottkochbrothers.com/),
much less every company on the
[HRC Buyer's Guide](http://www.hrc.org/apps/buyersguide/). And, sure, in
the case of the HRC Buyer's Guide,
[there's an app for that](http://bit.ly/BuyersGuideiPhone) if you're cool
enough have an iPhone, but how many of these apps are you supposed to have?
What if you're buying stuff off Amazon?

My goal is to make a service that can aggregate all the different consumer
campaigns together in one place. If you see a campaign you believe in, you
can subscribe to it, and it'll be there to refer back to when you make
a purchasing decision. A service like this could be used to power
[Darcy Burner's hypothetical buying guide app](http://www.forbes.com/sites/clareoconnor/2012/06/18/microsoft-programmer-turned-democrat-politician-plans-anti-koch-brothers-smartphone-app/), an browser plugin for amazon.com and other
shopping sites, and any number of other things.

But before we can get every non-profit and well-meaning organization to
participate, we need to some data to bootstrap the project. Thus the humble
Parse Buying Guides project.

I need your help finding interesting buying guides on the web, and writing
scripts that convert them to some sort of JSON format. We'll work out the
details of the format as we go; right now we just need some structured data.

How to Help
===========

Finding Buying Guides
---------------------

Right now, I'm focusing on guides that are aimed at:
* consumers (not investors, workers, businesses, volunteers, etc. yet)
* who are in the U.S. (San Francisco especially)
* who are politically progressive (however you define that)

Basically, this needs to work for someone before it can work for everyone,
and I need to be able to dogfood it and test it out on my friends.

I need your help finding interesting guides with useful data. If you use
GitHub, submit pull requests for changes to `TODO.txt`. If you don't, just
email me at <dm@davidmarin.org>.

More criteria for guides:
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

My Plan
=======

My general plan is to start storing the outputs of these programs in some
sort of indexable JSON data store, probably
[CouchDB](http://couchdb.apache.org/) (though
[mongoDB](http://www.mongodb.org/) is on my radar as well).

Next, I'll make an initial API. I've come to terms with the fact that my API
probably won't be a pure Couch App (too many needs for joins, especially when
you get into users subscribing to campaigns; filtering by location is a bit
of a bear as well), but it might look a lot like Couch.

Finally, I'll make a mobile website that runs off the API. Initially, I'll
open it up to friends and people who contribute to this project, but as soon
as it doesn't suck, I'll open up it, and the API, to everybody. The API will be
writeable as well as readable; you'll be able to submit your own campaigns, and
organizations who created the campaigns parsed by this project will be able
to manage their own campaigns if they choose to do so.

Other applications that should follow soon after are:
* Chrome browser plugin for amazon.com.
* Android app that's similar to the website except it scans barcodes, and works
  offline (does your smartphone get good reception where you shop?).
* Web-based interface for creating and managing campaigns.

I *think* I can make this work as a business (or at least pay for server
costs). If I learned anything from working at Yelp, it's that if people are
using your site to make buying decisions, there's money to be made somewhere.

However, I consider myself a bit of a "nontrepreneur". I know that starting
a business is a powerful way to change the world, but I also know that it's a
tremendous amount of work, work that should only be taken on if no one else
will do it (or do it right). If I could turn all my business ideas into
businesses [like this](http://xkcd.com/1060/), I probably would.

If this *is* something you're serious about wanting to take on,
[contact me](dm@davidmarin.org), and I'll probably help you out, maybe even
invest in your company or serve on the board. If not, hey, I'm a competent guy,
and I'll do what needs to be done. :)

Thanks for your help!
