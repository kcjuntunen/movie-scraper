#!/usr/bin/python

import sys
from bs4 import BeautifulSoup
import urllib3

ROOT = 'http://www.imdb.com'


def get_list(movie):
    timeout = urllib3.Timeout(connect=2.0, read=10.0)
    http = urllib3.PoolManager(timeout=timeout)
    result = http.request('GET',
                          '{0}/find/'.format(ROOT, ),
                          fields={"q": movie})
    if result.status == 200:
        return result.data


def get_page(link):
    timeout = urllib3.Timeout(connect=2.0, read=10.0)
    http = urllib3.PoolManager(timeout=timeout)
    result = http.request('GET', link)
    if result.status == 200:
        return result.data


def get_page_link(movie):
    soup = BeautifulSoup(get_list(movie), 'html.parser')
    findList = soup.find_all('table', {'class': 'findList'})
    link = '{0}{1}'.format(ROOT, findList[0].a.attrs['href'])
    return link


def get_rating(page):
    soup = BeautifulSoup(page, 'html.parser')
    rating = soup.find('span', {'itemprop': 'contentRating'})
    return rating.text


def get_title(page):
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('h1', {'itemprop': 'name'})
    return title.text


def get_year(page):
    soup = BeautifulSoup(page, 'html.parser')
    year = soup.find('span', {'id': 'titleYear'})
    return year.text


def get_rating_value(page):
    soup = BeautifulSoup(page, 'html.parser')
    rating_value = soup.find('span', {'itemprop': 'ratingValue'})
    return rating_value.text

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
    movie = ' '.join(sys.argv[1:])
    page_link = get_page_link(movie)
    page = get_page(page_link)
    name = get_title(page)
    rating = get_rating(page)
    rtg_val = (float(get_rating_value(page)) * 10.0)
    adv_link = get_parental_advisory_link(page)
    adv_page = get_page(adv_link)
    print('Title: {0}'.format(name))
    print('Certification: {0}'.format(rating, ))
    print('Rating {0:.0f}%'.format(rtg_val, ))
    print('-' * 40)
    found_advisories = get_parental_advisory(adv_page)
    for advisory in found_advisories:
        print('{0}: {1}'.format(advisory, found_advisories[advisory],))
