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

import re
import sys
from optparse import OptionParser

from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from pyassert import assert_that
from urlparse import urlparse
from urlparse import parse_qsl

from pbg.common.microdata import Item


RATING_COLOR_TO_JUDGMENT_TYPE = {
    'green': 'Good',
    'yellow': 'Mixed',
    'red': 'Bad',
}
# TODO: parse this from the document
CAMPAIGN_AUTHOR = 'Human Rights Campaign'
CAMPAIGN_NAME = "Buyer's Guide"
WHITESPACE_RE = re.compile('\s+')


def main():
    _, args = OptionParser().parse_args()
    assert_that(args).is_not_empty()

    judgments = []
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
            judgments.extend(parse_category_page_divs(divs))

    assert_that(description).is_not_none()

    judgments = merge_judgments_by_company_name(judgments)

    author = Item('NGO')
    author.set('name', CAMPAIGN_AUTHOR)

    guide = Item('BuyersGuide')
    guide.set('author', author)
    guide.set('name', CAMPAIGN_NAME)
    guide.set('description', description)
    guide.props['judgment'] = judgments

    sys.stdout.write(guide.json())


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
    responded_to_survey = not(company_p.em)

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

    brands = []

    for brand_name in brand_names:
        brand = Item('Brand')
        brand.set('name', brand_name)
        brand.set('category', category_name)
        brand.extra['hrcCategoryID'] = hrc_catid
        brands.append(brand)

    target = Item('Corporation')
    target.set('name', company_name)
    target.props['brand'] = brands
    target.set('category', category_name)
    target.extra['hrcOrgID'] = hrc_orgid
    target.extra['hrcCategoryID'] = [hrc_catid]

    judgment = Item('Judgment')
    judgment.set('target', target)
    judgment.set('judgment', RATING_COLOR_TO_JUDGMENT_TYPE[color])
    judgment.set('name', '%d out of 100' % rank)

    if not responded_to_survey:
        judgment.set('caveat', 'Did not respond to survey')
    elif is_partner or partner_brands:
        # pretty sure you have to respond to the survey to be a partner :)
        judgment.set('caveat', 'HRC National Corporate Partner')

    judgment.extra['rank'] = rank
    judgment.extra['isHrcPartner'] = is_partner
    if partner_brands:
        judgment.extra['hrcPartnerBrand'] = partner_brands
    judgment.extra['respondedToSurvey'] = responded_to_survey

    return judgment


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


def merge_judgments_by_company_name(judgments):
    cn_to_judgment = {}

    for j in judgments:
        cn = j.get('target').get('name')

        if cn in cn_to_judgment:
            old_j = cn_to_judgment[cn]

            safe_update(old_j.extra, j.extra, merge=['hrcPartnerBrand'])

            safe_update(old_j.get('target').extra, j.get('target').extra,
                        merge=['hrcCategoryID'])
            safe_update(old_j.get('target').props, j.get('target').props,
                        merge=['brand', 'category'])

            safe_update(old_j.props, j.props, skip=['target'])
        else:
            cn_to_judgment[cn] = j

    results = [j for (cn, j) in sorted(cn_to_judgment.iteritems())]

    for j in results:
        if j.extra.get('hrcPartnerBrand'):
            j.extra['hrcPartnerBrand'].sort()
        j.get('target').get_all('brand').sort(key=lambda b: b.get('name'))
        j.get('target').get_all('category').sort()

    return results


def safe_update(dest, src, merge=(), skip=()):
    for k in src:
        if k in skip:
            return
        elif k in merge:
            if k in dest or k in src:
                dest.setdefault(k, [])
                dest[k].extend(src.get(k, []))
        elif k in dest:
            assert_that(src[k]).equals(dest[k])
        else:
            dest[k] = src[k]


if __name__ == '__main__':
    main()
