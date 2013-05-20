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


def main():
    _, args = OptionParser().parse_args()
    assert_that(len(args)).equals(1)
    with open(args[0]) as f:
        html = f.read()

    # use html5lib, as the default parser excludes almost all of the body
    soup = BeautifulSoup(html, 'html5lib')
    judgments = []

    table = soup.find('table', {'id': 'organic-egg-scorecard'})

    trs = table.find_all('tr')
    assert len(trs) > 20

    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 6:
            judgment = Item('Judgment')
            if not tds[0].a:
                continue

            brand_name = tds[0].a.string.strip()
            company_name = tds[0].i.string
            assert_that(company_name).starts_with('by ')
            company_name = company_name[3:].strip()

            brand = Item('Brand')
            brand.set('name', brand_name)

            target = Item('Corporation')
            target.set('name', company_name)
            target.set('brand', brand)

            judgment.set('target', target)

            rating = int(tds[1].string)
            if rating >= 3:
                judgment_type = 'Good'
            elif rating == 2:
                judgment_type = 'Mixed'
            else:
                judgment_type = 'Poor'

            judgment.set('judgment', judgment_type)
            judgment.set('name', '%d out of 5' % rating)

            location = tds[2].string
            if location and location.strip():
                parts = location.strip().split(', ')
                assert_that(len(parts)).ge(1).le(2)

                addr = Item('PostalAddress')
                # this guide only covers US companies
                addr.set('addressCountry', 'US')

                state = parts[-1]
                if len(state) != 2:
                    assert_that(STATE_NAME_TO_ABBR).contains(state)
                    state = STATE_NAME_TO_ABBR[state].upper()
                addr.set('region', state)

                if len(parts) == 2:
                    addr.set('locality', parts[0])

                target.set('location', addr)

            market_area = tds[3].string
            if market_area and market_area.strip():
                # TODO: parse this and add it to the "spatial" field
                judgment.extra['market_area'] = market_area

            judgment.extra['total_score'] = int(tds[4].string)

            judgments.append(judgment)

    assert len(judgments) > 20

    author = Item('NGO')
    # TODO: parse this from the document
    author.set('name', 'Organic Egg Scorecard')

    guide = Item('BuyersGuide')
    guide.set('author', author)
    # TODO: parse this from document
    guide.set('name', 'Organic Egg Scorecard')
    guide.props['judgment'] = judgments

    sys.stdout.write(guide.json())


if __name__ == '__main__':
    main()
