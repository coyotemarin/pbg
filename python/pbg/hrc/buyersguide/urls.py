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
"""Scrape URLs from the HRC buying guide main page.

usage:

ROOT_URL=http://www.hrc.org/apps/buyersguide
curl -L --compressed $ROOT_URL > hrc.html
python -m pbg.hrc.buyersguide.urls hrc.html > hrc-urls.txt

See data.py for what to do next
"""
from __future__ import with_statement

from optparse import OptionParser

from bs4 import BeautifulSoup
from pyassert import assert_that
from urllib import urlencode


def main():
    _, args = OptionParser().parse_args()
    assert_that(len(args)).equals(1)
    with open(args[0]) as f:
        soup = BeautifulSoup(f.read())

    selected_options = soup.select(
        '#content div.legislation-box form option[selected]')
    assert_that(selected_options).is_not_empty()

    for selected_option in selected_options:
        # not worth fetching a page for each company; this is slow
        # and the extra info isn't that useful
        if selected_option.string.strip() != 'by Category':
            continue

        form = None
        for parent in selected_option.parents:
            if parent.name == 'form':
                form = parent
                break

        action = form['action']

        selects = form.select('select')
        assert_that(len(selects)).equals(1)

        name = selects[0]['name']

        options = form.select('option[value]')
        assert_that(len(options)).gt(10)

        for option in options:
            url = action + '?' + urlencode({name: option['value']})
            print url

        return

    raise AssertionError('could not find "by Company" dropdown')


if __name__ == '__main__':
    main()
