"""usage:

ROOT_URL=http://www.hrc.org/apps/buyersguide
curl -L --compressed $ROOT_URL > hrc.html
python -m mbg.hrc.buyersguide.urls hrc.html > hrc-urls.txt

rm -rf hrc-pages
mkdir hrc-pages
for path in $(cat hrc-urls.txt)
    do curl -L --compressed $ROOT_URL/$path > hrc-pages/$path.html
done
python -m mbg.hrc.buyersguide.data hrc.html hrc-pages/*.html > hrc.json
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


RATING_COLOR_TO_SHOULD_BUY = {
    'green': 'yes',
    'yellow': 'maybe',
    'red': 'no',
}
CAMPAIGN_NAME = "Human Rights Campaign Buyer's Guide"
WHITESPACE_RE = re.compile('\s+')


def main():
    _, args = OptionParser().parse_args()
    assert_that(args).is_not_empty()

    entries = []
    about = None

    for path in args:
        with open(path) as f:
            soup = BeautifulSoup(f.read(), 'html5lib')

        content = soup.select('#content')[0]

        divs = content.select('div')

        # main page
        if len(divs) == 1:
            assert_that(content.h1.string.lower()).equals('about the guide')
            about = parse_about(content)
        # category page
        else:
            assert_that(len(divs)).equals(2)
            entries.extend(parse_category_page_divs(divs))

    assert_that(about).is_not_none()

    entries = merge_entries_by_company_name(entries)

    result = {
        'name': CAMPAIGN_NAME,
        'about': about,
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

    category_desc = divs[1].h2.string

    trs = divs[1].select('table tbody tr')

    assert_that(trs[0].td.p.strong.string).equals('Business')

    for tr in trs[1:]:
        yield parse_category_page_tr(tr, category_desc)


def parse_category_page_tr(tr, category_desc):
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

    responded = not(company_p.i)

    partner = bool(company_p.img)
    if partner:
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
        'desc': category_desc,
        'x_hrc_catid': hrc_catid,
    }

    brands = [{'name': bn, 'categories': [category]} for bn in brand_names]

    return {
        'target': {
            'type': 'company',
            'name': company_name,
            'brands': brands,
            'categories': [category],
            'x_hrc_orgid': hrc_orgid,
        },
        'ratings': {
            'color': color,
            'rank': rank,
            'responded': responded,
            'partner': partner,
            'partner_brands': partner_brands,
        },
        'actions': {
            'buy': RATING_COLOR_TO_SHOULD_BUY[color],
        },
    }


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
    for color in RATING_COLOR_TO_SHOULD_BUY:
        if color in img_src:
            return color

    raise AssertionError('unknown color for image: ' + img_src)


def merge_entries_by_company_name(entries):
    cn_to_entry = {}

    for entry in entries:
        cn = entry['target']['name']

        if cn in cn_to_entry:
            old_entry = cn_to_entry[cn]
            old_entry['ratings']['partner_brands'].extend(
                entry['ratings']['partner_brands'])
            del entry['ratings']['partner_brands']
            safe_update(old_entry['ratings'], entry['ratings'])
            old_entry['target']['brands'].extend(
                entry['target']['brands'])
            old_entry['target']['categories'].extend(
                entry['target']['categories'])
        else:
            cn_to_entry[cn] = entry

    results = sorted(cn_to_entry.itervalues(),
                           key=lambda i: i['target']['name'])

    for entry in results:
        entry['ratings']['partner_brands'].sort()
        entry['target']['brands'].sort(key=lambda b: b['name'])
        entry['target']['categories'].sort(key=lambda c: c['desc'])

    return results


def safe_update(dest, src):
    for k in src:
        if k in dest:
            assert_that(src[k]).equals(dest[k])
        else:
            dest[k] = src[k]


if __name__ == '__main__':
    main()
