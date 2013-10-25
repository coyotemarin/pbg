# Copyright 2013 David Marin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""usage:

curl http://www.cornucopia.org/organic-egg-scorecard/ > eggs.html
python -m pbg.cornucopia.eggs eggs.html
"""
import sys
from optparse import OptionParser


from bs4 import BeautifulSoup
from pyassert import assert_that


from pbg.common.microdata import Item


STATE_NAME_TO_ABBR = {
    'Michigan': 'MI',
    'Nebraska': 'NE',
    'Utah': 'UT',
}


def add_itemscope(element, itemtype):
    element['itemscope'] = None
    element['itemtype'] = itemtype


def add_itemprop(element, name, itemtype=None):
    element['itemprop'] = name
    if itemtype:
        add_itemscope(element, itemtype)


def add_itemref(element, destElement):
    add_id(destElement)
    if element.get('itemref'):
        refs = set(element['itemref'].split())
        refs.add(destElement['id'])
        element['itemref'] += ' '.join(sorted(refs))
    else:
        element['itemref'] = destElement['id']


def add_id(element):
    if element.get('id'):
        return
    if not hasattr(add_id, 'next_id'):
        add_id.next_id = 0
    element['id'] = '%05d' % add_id.next_id
    add_id.next_id += 1


def main():
    _, args = OptionParser().parse_args()
    assert_that(len(args)).equals(1)
    with open(args[0]) as f:
        html = f.read()

    # use html5lib, as the default parser excludes almost all of the body
    soup = BeautifulSoup(html, 'html5lib')

    # the whole thing is the Buyer's Guide
    add_itemscope(soup.body, 'BuyersGuide')

    # find the name of the Buyer's Guide
    name_spans = soup.select('table table span.style26')
    assert_that(len(name_spans)).equals(1)
    add_itemprop(name_spans[0], 'name')

    scorecard_table = soup.find('table', {'id': 'organic-egg-scorecard'})

    trs = scorecard_table.find_all('tr')
    assert_that(len(trs)).is_greater_than(20)

    # skip the column headers
    for tr in trs[1:]:
        tds = tr.find_all('td')
        if len(tds) == 1:
            add_itemprop(tr, 'judgment', 'BuyersGuideJudgment')

            add_itemprop(tds[0].strong, 'name')
            add_itemprop(tds[0].normal, 'description')
        else:
            assert_that(len(tds)).equals(6)

            add_itemprop(tr, 'reviewOfTarget', 'http://schema.org/Review')

            # first column contains brand and company name
            add_itemprop(tds[0], 'itemReviewed', 'http://schema.org/Brand')

            name_a = tds[0].a
            add_itemprop(name_a, 'infoUrl')
            name_span = name_a.string.wrap(soup.new_tag('span'))
            add_itemprop(name_span, 'name')

            add_itemprop(tds[0].i, 'brandOf', 'http://schema.org/Company')

            assert_that(len(tds[0].i.contents)).equals(1)
            company_str = tds[0].i.contents[0]
            assert_that(company_str).starts_with('by ')
            company_name_span = soup.new_tag('span')
            company_name_span.string = company_str[3:]
            tds[0].i.string = company_str[:3]
            tds[0].i.append(company_name_span)
            add_itemprop(company_name_span, 'name')

            # second column contains rating
            add_itemprop(tds[1], 'reviewRating', 'http://schema.org/Rating')
            rating_span = tds[1].string.wrap(soup.new_tag('span'))
            add_itemprop(rating_span, 'ratingValue')

            # third column contains company location
            if tds[2].string:
                add_itemprop(tds[2], 'location', 'http://schema.org/Place')
                place_name_span = tds[2].string.wrap(soup.new_tag('span'))
                # don't bother parsing location, for now
                add_itemprop(place_name_span, 'description')
                add_itemref(tds[0].i, place_name_span)

            # fourth column contains market location
            if tds[3].string:
                add_itemprop(tds[3], 'spatial', 'http://schema.org/Place')
                market_span = tds[3].string.wrap(soup.new_tag('span'))
                # don't bother parsing location, for now
                add_itemprop(market_span, 'description')


    # TODO: add organization info and donateUrl

    print soup


if __name__ == '__main__':
    main()
