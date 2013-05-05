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

ROOT_URL=http://www.hrc.org/apps/buyersguide
curl -L --compressed $ROOT_URL > hrc.html
python -m pbg.hrc.buyersguide.urls hrc.html > hrc-urls.txt

rm -rf hrc-pages
mkdir hrc-pages
for path in $(cat hrc-urls.txt)
    do curl -L --compressed $ROOT_URL/$path > hrc-pages/$path.html
done
python -m pbg.hrc.buyersguide.data hrc.html hrc-pages/*.html > hrc.json
"""
# TODO: parse http://www.hrc.org/apps/buyersguide/how-to-use.php
# and include info on what the ratings mean
from __future__ import with_statement

import json
import re
import sys
from optparse import OptionParser

from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from pyassert import assert_that
from urlparse import urlparse
from urlparse import parse_qsl


RATING_COLOR_TO_JUDGMENT_TYPE = {
    'green': 'Good',
    'yellow': 'Mixed',
    'red': 'Bad',
}
CAMPAIGN_AUTHOR =  {
    'type': 'NGO',
    'name': 'Human Rights Campaign',
}
CAMPAIGN_NAME = "Buyer's Guide"
WHITESPACE_RE = re.compile('\s+')


def main():
    _, args = OptionParser().parse_args()
    assert_that(args).is_not_empty()

    entries = []
    description = None

    for path in args:
        with open(path) as f:
            soup = BeautifulSoup(f.read(), 'html5lib')

        content = soup.select('#content')[0]

        divs = content.select('div')

        # main page
        if len(divs) == 1:
            assert_that(content.h1.string.lower()).equals('about the guide')
            description = parse_about(content)
        # category page
        else:
            assert_that(len(divs)).equals(2)
            entries.extend(parse_category_page_divs(divs))

    assert_that(description).is_not_none()

    entries = merge_entries_by_company_name(entries)

    result = {
        'author': CAMPAIGN_AUTHOR,
        'name': CAMPAIGN_NAME,
        'description': description,
        'entries': entries,
    }

    json.dump(result, sys.stdout, sort_keys=True, indent=4)


def parse_about(content):
    paragraphs = []
    for p in content.select('> p'):
        if p.string:
            paragraph = fix_whitespace(p.string)
            if paragraph:
                paragraphs.append(paragraph)

    return '\n\n'.join(paragraphs)


def fix_whitespace(s):
    return WHITESPACE_RE.sub(' ', s).strip()


def parse_category_page_divs(divs):
    assert_that(divs[0].h2.string.lower()).equals('search')

    category_name = divs[1].h2.string

    trs = divs[1].select('table tbody tr')

    assert_that(trs[0].td.p.strong.string).equals('Business')

    for tr in trs[1:]:
        yield parse_category_page_tr(tr, category_name)


def parse_category_page_tr(tr, category_name):
    tds = tr.select('td')
    assert_that(len(tds)).equals(3)

    # parse the link
    biz_td = tds[0]
    ps = biz_td.select('p')

    assert_that(len(ps)).ge(1)
    assert_that(len(ps)).le(2)

    company_p = ps[0]
    href = company_p.a['href']
    href_query = urlparse(href).query
    href_params = dict(parse_qsl(href_query))

    hrc_catid = href_params['catid']
    hrc_orgid = href_params['orgid']

    company_name = company_p.a.strong.string

    responded_to_survey = not(company_p.i)

    is_partner = bool(company_p.img)
    if is_partner:
        assert_is_partner_img(company_p.img)

    if len(ps) >= 2:
        brand_p = ps[1]
        brand_names, partner_brands = parse_brand_p(brand_p)
    else:
        # AIX Armani Exchange doesn't have brands listed, for example
        brand_names = []
        partner_brands = []

    rating_td = tds[1]
    color = parse_img_src_rating_color(rating_td.img['src'])

    rank_td = tds[2]
    rank_strings = list(rank_td.p.stripped_strings)
    assert_that(len(rank_strings)).equals(1)
    rank = int(rank_strings[0])

    category = {
        'name': category_name,
        'hrc_catid': hrc_catid,
    }

    brands = []

    for brand_name in brand_names:
        brands.append({
            'type': 'Brand',
            'name': brand_name,
            'extra': {
                'category': category,
                'is_hrc_partner': is_partner or brand_name in partner_brands,
            }
        })

    judgment = RATING_COLOR_TO_JUDGMENT_TYPE[color]

    rec = {
        'target': {
            'type': 'Corporation',
            'name': company_name,
            'brand': brands,
            'extra': {
                'category': [category],
                'hrc_orgid': hrc_orgid,
            },
        },
        'judgment': {
            'type': 'Enumeration/Judgment/' + judgment,
            'name': '%d out of 100' % rank,
            'extra': {
                'rank': rank,
                'is_hrc_partner': is_partner,
                'hrc_partner_brand': partner_brands,
                'responded_to_survey': responded_to_survey,
            },
        }
    }

    if not responded_to_survey:
        rec['judgment']['caveat'] = 'did not respond to survey'

    return rec


def parse_brand_p(p):
    brand_names = []
    # apparently brands can partner with HRC too. They don't get the CSS right
    # for this on their website (img floats left), but whatever
    partner_brands = []
    is_partner = False

    for c in p.children:
        if type(c) == Tag and c.name == 'img':
            assert_is_partner_img(c)
            is_partner = True

        elif type(c) == NavigableString:
            brand_name = fix_whitespace(unicode(c))
            if brand_name:
                brand_names.append(brand_name)
                if is_partner:
                    partner_brands.append(brand_name)
                    is_partner = False

    return brand_names, partner_brands


def assert_is_partner_img(img):
    assert_that(img['src']).contains('blue')


def parse_img_src_rating_color(img_src):
    for color in RATING_COLOR_TO_JUDGMENT_TYPE:
        if color in img_src:
            return color

    raise AssertionError('unknown color for image: ' + img_src)


def merge_entries_by_company_name(entries):
    cn_to_entry = {}

    for entry in entries:
        cn = entry['target']['name']

        if cn in cn_to_entry:
            old_entry = cn_to_entry[cn]
            old_entry['judgment']['extra']['hrc_partner_brand'].extend(
                entry['judgment']['extra']['hrc_partner_brand'])
            entry['judgment']['extra']['hrc_partner_brand'] = (
                old_entry['judgment']['extra']['hrc_partner_brand'])
            safe_update(old_entry['judgment'], entry['judgment'])
            old_entry['target']['brand'].extend(
                entry['target']['brand'])
            old_entry['target']['extra']['category'].extend(
                entry['target']['extra']['category'])
        else:
            cn_to_entry[cn] = entry

    results = sorted(cn_to_entry.itervalues(),
                           key=lambda i: i['target']['name'])

    for entry in results:
        entry['judgment']['extra']['hrc_partner_brand'].sort()
        entry['target']['brand'].sort(key=lambda b: b['name'])
        entry['target']['extra']['category'].sort(key=lambda c: c['name'])

    return results


def safe_update(dest, src):
    for k in src:
        if k in dest:
            assert_that(src[k]).equals(dest[k])
        else:
            dest[k] = src[k]


if __name__ == '__main__':
    main()
