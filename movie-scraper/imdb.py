#!/usr/bin/python

import sys
import textwrap
from bs4 import BeautifulSoup
import urllib3

ROOT = 'http://www.imdb.com'

HEADERS = {'accept':
           'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'accept-encoding': 'gzip, deflate, br',
           'accept-language': 'en-US,en;q=0.8',
           'cache-control': 'max-age=0',
           'dnt': '1',
           'upgrade-insecure-requests': '1',
           'user-agent':
           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/60.0.3112.78 '
           'Safari/537.36 OPR/47.0.2631.55', }

GREEN = '\033[1;32;99m'
NORMAL = '\033[0m'


def req(url, **kwargs):
    fields = kwargs.get('fields', {})
    timeout = urllib3.Timeout(connect=2.0, read=10.0)
    http = urllib3.PoolManager(timeout=timeout)
    result = http.request('GET',
                          url,
                          fields=fields,
                          headers=HEADERS)
    if result.status == 200:
        return BeautifulSoup(result.data, 'html.parser')


def get_list(movie):
    return req('{0}/find/'.format(ROOT, ), fields={"q": movie})


def get_page(link):
    return req(link)


def get_page_link(soup):
    findlist = soup.find_all('table', {'class': 'findList'})
    link = '{0}{1}'.format(ROOT, findlist[0].a.attrs['href'])
    return link

def get_cert(soup):
    rating = soup.find_all('div', {'class': 'txt-block'})
    for r in rating:
        if 'ertif' in r.text:
            substrings = r.text.split('\n')
            if len(substrings) > 2:
                return substrings[2]
    return "[Nothin']"

def get_title(soup):
    title = soup.find('h1', {'class': ''})
    if title is not None:
        return title.text
    return "[Can't figure out title]"

def get_synopsis(soup):
    synop = soup.find('div', {'class': 'summary_text'})
    return synop.text.strip()



def get_year(soup):
    year = soup.find('span', {'id': 'titleYear'})
    return year.text


def get_rating_value(soup):
    rating_value = soup.find('span', {'itemprop': 'ratingValue'})
    if rating_value is not None:
        return rating_value.text

def get_parental_advisory_link(soup):
    linkdata = soup.find_all('div', {'class': 'quicklinkSectionItem'})
    for link in linkdata:
        if 'parent' in link.a.attrs['href']:
            return '{0}{1}'.format(ROOT, link.a.attrs['href'])
    return ''

def get_parental_advisory(soup):
    advisories = {}
    sections = soup.find_all('section')
    for section in sections:
        if 'id' in section.attrs.keys():
            if 'advisory' in section.attrs['id']:
                title = section.find('h4').text
                j = section.find_all('li', attrs={'class': 'ipl-zebra-list__item'})
                if len(j) < 1:
                    return advisories
                k = j[0]
                advisories[title] = k.text.replace('Edit', '').replace('\n', '').strip()
    return advisories


def render_output():
    print('-' * 72)
    wrapper = textwrap.TextWrapper(width=79, subsequent_indent=(' ' * 32))
    movielookup = ' '.join(sys.argv[1:])
    page_link = get_page_link(get_list(movielookup))
    imdbpage = get_page(page_link)
    name = get_title(imdbpage)
    certification = get_rating(imdbpage)
    rtg_val = (float(get_rating_value(imdbpage)) * 10.0)
    adv_link = get_parental_advisory_link(imdbpage)
    adv_page = get_page(adv_link)
    print('{}{:>30}{}: {}'.format(GREEN, 'Title', NORMAL, name))
    print('{}{:>30}{}: {}'.format(GREEN, 'Certification', NORMAL, certification, ))
    print('{}{:>30}{}: {}'.format(GREEN, 'Synopsis', NORMAL, wrapper.fill(get_synopsis(imdbpage))))
    print('{}{:>30}{}: {:.0f}%'.format(GREEN, 'Rating', NORMAL, rtg_val, ))
    found_advisories = get_parental_advisory(adv_page)
    for advisory in found_advisories:
        print('{}{:>30}{}: {}'.format(GREEN, advisory, NORMAL,
                                      wrapper.fill(found_advisories[advisory]),))
    print('-' * 72)


if __name__ == "__main__":
    render_output()
