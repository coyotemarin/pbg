# usage:
# curl http://www.cornucopia.org/organic-egg-scorecard/ > eggs.html
# python -m mbg.cornucopia.eggs < eggs.html
import json
import sys

from bs4 import BeautifulSoup


def main():
    html = sys.stdin.read()
    # use html5lib, as the default parser excludes almost all of the body
    soup = BeautifulSoup(html, 'html5lib')
    ratings = []

    table = soup.find('table', {'id': 'organic-egg-scorecard'})

    trs = table.find_all('tr')
    assert len(trs) > 20

    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 6:
            rating = {}
            if not tds[0].a:
                continue

            rating['brand'] = tds[0].a.string.strip()
            company_name = tds[0].i.string
            if company_name.startswith('by '):
                company_name = company_name[3:].strip()
            else:
                raise Exception(company_name)
            rating['company'] = {'name': company_name}

            rating['rating'] = int(tds[1].string)
            location = tds[2].string
            if location and location.strip():
                rating['company']['location'] = location

            market_area = tds[3].string
            if market_area and market_area.strip():
                rating['markets'] = [{'desc': market_area,
                                      'country': 'US'}]
            rating['total_score'] = int(tds[4].string)

            ratings.append(rating)

    assert len(ratings) > 20

    json.dump({'ratings': ratings}, sys.stdout, sort_keys=True, indent=4)

if __name__ == '__main__':
    main()
