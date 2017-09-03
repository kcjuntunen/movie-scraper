#!/usr/bin/python

import sys
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
        return result.data


def get_list(movie):
    return req('{0}/find/'.format(ROOT, ), fields={"q": movie})


def get_page(link):
    return req(link)


def get_page_link(movie):
    soup = BeautifulSoup(get_list(movie), 'html.parser')
    findList = soup.find_all('table', {'class': 'findList'})
    link = '{0}{1}'.format(ROOT, findList[0].a.attrs['href'])
    return link


def get_rating(page):
    soup = BeautifulSoup(page, 'html.parser')
    rating = soup.find('meta', {'itemprop': 'contentRating'})
    if rating is None:
        rating = soup.find('span', {'itemprop': 'contentRating'})
    if rating is not None:
        if 'content' in rating.attrs:
            return rating.attrs['content']
        else:
            return rating.text
    return ''


def get_title(page):
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('h1', {'itemprop': 'name'})
    return title.text

def get_synopsis(page):
    soup = BeautifulSoup(page, 'html.parser')
    synop = soup.find('div', {'class': 'summary_text'})
    return synop.text.strip()



def get_year(page):
    soup = BeautifulSoup(page, 'html.parser')
    year = soup.find('span', {'id': 'titleYear'})
    return year.text


def get_rating_value(page):
    soup = BeautifulSoup(page, 'html.parser')
    rating_value = soup.find('span', {'itemprop': 'ratingValue'})
    if rating_value is not None:
        return rating_value.text
    else:
        return ''

def get_parental_advisory_link(page):
    soup = BeautifulSoup(page, 'html.parser')
    linkdata = soup.find_all('span', {'itemprop': 'audience'})
    link = '{0}{1}'.format(ROOT, linkdata[0].a.attrs['href'])
    return link


def get_parental_advisory(page):
    soup = BeautifulSoup(page, 'html.parser')
    advisories = {}
    sections = soup.find_all('section')
    for section in sections:
        if 'id' in section.attrs.keys():
            if 'advisory' in section.attrs['id']:
                title = section.find('h4').text
                j = section.find_all('li', attrs={'class': 'ipl-zebra-list__item'})[0]
                advisories[title] = j.text.replace('Edit', '').replace('\n', '').strip()
    return advisories


if __name__ == "__main__":
    movielookup = ' '.join(sys.argv[1:])
    page_link = get_page_link(movielookup)
    imdbpage = get_page(page_link)
    name = get_title(imdbpage)
    certification = get_rating(imdbpage)
    rtg_val = (float(get_rating_value(imdbpage)) * 10.0)
    adv_link = get_parental_advisory_link(imdbpage)
    adv_page = get_page(adv_link)
    print('{}Title{}: {}'.format(GREEN, NORMAL, name))
    print('{}Certification{}: {}'.format(GREEN, NORMAL, certification, ))
    print('{}Synopsis{}: {}'.format(GREEN, NORMAL, get_synopsis(imdbpage)))
    print('{}Rating{}: {:.0f}%'.format(GREEN, NORMAL, rtg_val, ))
    found_advisories = get_parental_advisory(adv_page)
    for advisory in found_advisories:
        print('{}{}{}: {}'.format(GREEN, advisory, NORMAL, found_advisories[advisory],))
    print('-' * 72)
