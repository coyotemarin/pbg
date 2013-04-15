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

curl http://www.hotelworkersrising.org/HotelGuide/results.php > hotels.html
python -m pbg.unitehere.uhg hotels.html
"""
import json
import re
import sys
from optparse import OptionParser

from bs4 import BeautifulSoup
from bs4 import Tag
from pyassert import assert_that


CATEGORY_TO_JUDGMENT = {
    'Please Patronize': 'Good',
    'Risk of Dispute': 'OK',
    'On Strike': 'Bad',
    'Boycott': 'Bad',
}

ADDRESS_RE = re.compile('^(.*), ([A-Z][A-Z]) (.*)$')


def main():
    _, args = OptionParser().parse_args()
    assert_that(len(args)).equals(1)
    with open(args[0]) as f:
        soup = BeautifulSoup(f.read())

    h1s = soup.select('h1')
    assert_that(len(h1s)).equals(1)
    name = h1s[0].string

    copyright_ps = soup.select('p.copyright')
    assert_that(len(copyright_ps)).equals(1)
    copyright_strings = list(copyright_ps[0].stripped_strings)
    assert_that(len(copyright_strings)).equals(1)
    the_word_copyright, _, copyrightYear, author = (
        copyright_strings[0].split(None, 3))
    assert_that(the_word_copyright).equals('Copyright')
    copyrightYear = int(copyrightYear)

    tables = soup.select('table div table')
    assert_that(len(tables)).equals(1)

    trs = tables[0].select('tr')
    assert_that(len(trs)).equals(2)

    tds = trs[0].select('td')
    assert_that(len(tds)).equals(2)

    recommendations = []

    for td in tds:
        category = None

        for child in td.children:
            if isinstance(child, Tag):
                if child.name == 'h3':
                    category = child.string.strip()
                elif child.name == 'p':
                    recommendations.append(parse_p(child, category))

    result = {
        'type': 'CreativeWork/BuyingGuideV1',
        'name': name,
        'author': author,
        'copyrightYear': copyrightYear,
        'copyrightHolder': author,
        'recommendation': recommendations,
    }

    json.dump(result, sys.stdout, sort_keys=True, indent=4)


def parse_p(p, category):
    judgment = CATEGORY_TO_JUDGMENT[category]

    lines = list(p.stripped_strings)
    assert_that(len(lines)).equals(4)

    name = lines[0]
    street = lines[1]
    locality, region, country, postal = parse_rest_of_addr(lines[2])
    assert_that(lines[3]).starts_with('Phone: ')
    phone = lines[3][7:]

    return {
        'buy': {
            'type': 'Enumeration/Judgment/' + judgment,
            'name': category,
        },
        'target': {
            'type': 'Hotel',
            'name': name,
            'address': {
                'streetAddress': street,
                'addressLocality': locality,
                'addressRegion': region,
                'addressCountry': country,
                'postalCode': postal,
                'telephone': phone,
            },
        }
    }


def parse_rest_of_addr(line):
    m = ADDRESS_RE.match(line)
    assert_that(m).is_true()
    locality = m.group(0)
    region = m.group(1)
    postal = m.group(2)
    country = 'US' if len(postal) == 5 else 'CA'

    return locality, region, country, postal


if __name__ == '__main__':
    main()
