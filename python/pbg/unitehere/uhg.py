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

curl http://www.hotelworkersrising.org/HotelGuide/results.php > uhg.html
python -m pbg.unitehere.uhg uhg.html
"""
import re
import sys
from optparse import OptionParser

from bs4 import BeautifulSoup
from bs4 import Tag
from microdata import Item
from pyassert import assert_that


CATEGORY_TO_JUDGMENT_TYPE = {
    'Please Patronize': 'Good',
    'Risk of Dispute': 'Mixed',
    'On Strike': 'Bad',
    'Boycott These Properties': 'Bad',
}

CATEGORY_TO_JUDGMENT_NAME = {
    'Boycott These Properties': 'Boycott',
}

CANADA_REGIONS = set(['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'ON',
                      'PE', 'QC', 'SK', 'NT', 'NU', 'YT'])

ADDRESS_RE = re.compile(
    '^(?P<locality>.*), (?P<region>[A-Z][A-Z])( (?P<postal>.*))?$')


def main():
    _, args = OptionParser().parse_args()
    assert_that(len(args)).equals(1)
    with open(args[0]) as f:
        html = f.read()

    # for some reason, the long ASP comment screws up BeautifulSoup,
    # so skip it
    start_index = html.find('<!DOCTYPE')
    assert_that(start_index).ge(0)

    soup = BeautifulSoup(html[start_index:], 'html5lib')

    h1s = soup.select('h1')
    assert_that(len(h1s)).equals(1)
    name = h1s[0].string

    copyright_ps = soup.select('p.copyright')
    assert_that(len(copyright_ps)).equals(1)
    copyright_strings = list(copyright_ps[0].stripped_strings)
    assert_that(len(copyright_strings)).equals(1)
    the_word_copyright, _, copyrightYear, author_name = (
        copyright_strings[0].split(None, 3))
    assert_that(the_word_copyright).equals('Copyright')
    copyrightYear = int(copyrightYear)
    author = Item('LaborUnion')
    author.set('name', author_name)

    tables = soup.select('table div table')
    assert_that(len(tables)).equals(1)

    trs = tables[0].select('tr')
    assert_that(len(trs)).equals(2)

    tds = trs[0].select('td')
    assert_that(len(tds)).equals(2)

    judgments = []

    for td in tds:
        category = None

        for child in td.children:
            if isinstance(child, Tag):
                if child.name == 'h3':
                    category = child.string.strip()
                elif child.name == 'p':
                    judgments.append(parse_p(child, category))

    guide = Item('BuyersGuide')
    guide.set('name', name)
    guide.set('author', author)
    guide.set('copyrightYear', copyrightYear)
    guide.set('copyrightHolder', author)
    guide.props['judgment'] = judgments

    sys.stdout.write(guide.json())


def parse_p(p, category):
    judgment_type = CATEGORY_TO_JUDGMENT_TYPE[category]
    judgment_name = CATEGORY_TO_JUDGMENT_NAME.get(category) or category

    lines = list(p.stripped_strings)
    assert_that(len(lines)).ge(2).le(4)

    name = lines[0]
    if name.endswith(' - ON STRIKE'):
        name = name[:-12]

    if len(lines) <= 2:
        address = parse_addr(lines[1:2])
    else:
        address = parse_addr(lines[1:3])

    if len(lines) >= 4:
        assert_that(lines[3]).starts_with('Phone: ')
        address.set('telephone', lines[3][7:])

    hotel = Item('Hotel')
    hotel.set('name', name)
    hotel.set('address', address)

    judgment = Item('Judgment')
    judgment.set('judgment', judgment_type)
    judgment.set('name', judgment_name)
    judgment.set('target', hotel)

    return judgment


def parse_addr(lines):
    assert_that(len(lines)).ge(1).le(2)

    addr = Item('PostalAddress')

    if len(lines) >= 2:
        addr.set('streetAddress', lines[0])

    m = ADDRESS_RE.match(lines[-1])
    assert_that(m).is_true()

    addr.set('locality', m.group('locality'))
    addr.set('region', m.group('region'))
    addr.set('addressCountry',
        'CA' if m.group('region') in CANADA_REGIONS else 'US')

    if m.group('postal'):
        addr.set('postalCode', m.group('postal'))

    return addr


if __name__ == '__main__':
    main()
