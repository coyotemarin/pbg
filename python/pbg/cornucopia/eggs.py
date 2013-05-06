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
import json
import sys
from optparse import OptionParser


from bs4 import BeautifulSoup
from pyassert import assert_that


# TODO: parse these out of the document
HARD_CODED_FIELDS = {
    'type': 'CreativeWork/BuyingGuideV1',
    'name': 'Organic Egg Scorecard',
    'author': {
        'type': 'Organization/NGO',
        'name': 'The Cornucopia Institute',
    },
}

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
    recs = []

    table = soup.find('table', {'id': 'organic-egg-scorecard'})

    trs = table.find_all('tr')
    assert len(trs) > 20

    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 6:
            rec = {}
            if not tds[0].a:
                continue

            brand_name = tds[0].a.string.strip()
            company_name = tds[0].i.string
            assert_that(company_name).starts_with('by ')
            company_name = company_name[3:].strip()

            rec['target'] = {
                'type': 'Corporation',
                'name': company_name,
                'brand': {
                    'type': 'Brand',
                    'name': brand_name,
                },
            }

            rating = int(tds[1].string)
            if rating >= 3:
                judgment_type = 'Good'
            elif rating == 2:
                judgment_type = 'Mixed'
            else:
                judgment_type = 'Poor'

            rec['judgment'] = {
                'type': 'Enumeration/Judgment/' + judgment_type,
                # TODO: parse rating descriptions for each section
                'name': '%d out of 5' % rating,
                'extra': {},
            }

            location = tds[2].string
            if location and location.strip():
                parts = location.strip().split(', ')
                assert_that(len(parts)).ge(1).le(2)
                place = {
                    'type': 'PostalAddress',
                    'addressCountry': 'US',
                }
                state = parts[-1]
                if len(state) != 2:
                    assert_that(STATE_NAME_TO_ABBR).contains(state)
                    state = STATE_NAME_TO_ABBR[state]
                place['region'] = state.upper()
                if len(parts) == 2:
                    place['locality'] = parts[0]

                rec['target']['location'] = location


            market_area = tds[3].string
            if market_area and market_area.strip():
                # TODO: parse this and add it to the "spatial" field
                rec['target'].setdefault('extra', {})
                rec['target']['extra']['market_area'] = market_area

            rec['judgment']['extra']['total_score'] = int(tds[4].string)

            recs.append(rec)

    assert len(recs) > 20

    guide = HARD_CODED_FIELDS.copy()
    guide['recommendation'] = recs

    json.dump(guide, sys.stdout, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()
