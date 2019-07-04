"""
An object that parses an ImdbPage and exposes its content.
"""
from os import linesep
from textwrap import TextWrapper
from bs4 import BeautifulSoup
from urllib3 import Timeout, PoolManager

ROOT = 'http://www.imdb.com'

HEADERS = {'accept':
           'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,'
           'image/apng,*/*;q=0.8',

           'accept-encoding': 'gzip, deflate, br',

           'accept-language': 'en-US,en;q=0.8',

           'cache-control': 'max-age=0',

           'dnt': '1',

           'upgrade-insecure-requests': '1',

           'user-agent':
           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
           '(KHTML, like Gecko) '
           'Chrome/60.0.3112.78 '
           'Safari/537.36 OPR/47.0.2631.55', }

GREEN = '\033[1;32;99m'
NORMAL = '\033[0m'


def request(url, **kwargs):
    """
    Return a BeautifulSoup object by downloading `url`.
    """
    fields = kwargs.get('fields', {})
    timeout = Timeout(connect=2.0, read=10.0)
    http = PoolManager(timeout=timeout)
    result = http.request('GET',
                          url,
                          fields=fields,
                          headers=HEADERS)
    if result.status == 200:
        return BeautifulSoup(result.data, 'html.parser')
    return None


class ImdbPage():
    """Represnts IMDB page data."""

    # pylint: disable=too-many-instance-attributes
    # This is the stuff I want from the page. Maybe I should
    # create some type of base object to hold them all?
    def __init__(self, search_term):
        self.search_term = search_term
        self.raw_data = None
        self.page_link = None
        self.__title = None
        self.__synopsis = None
        self.__certification = None
        self.rating_value = None
        self.advisory_link = None
        self.__advisories = None
        self.advisory_page = None
        self.__year = None
        self.__search()

    def __search(self):
        movie_list = request('{0}/find/'.format(ROOT, ),
                             fields={"q": self.search_term})
        self.__get_page_link(movie_list)
        self.__get_page()

    def __get_page(self):
        self.raw_data = request(self.page_link)

    def __get_page_link(self, soup):
        findlist = soup.find_all('table', {'class': 'findList'})
        self.page_link = '{0}{1}'.format(ROOT, findlist[0].a.attrs['href'])

    def __get_parental_advisory_link(self):
        if self.advisory_link is None:
            linkdata = self.raw_data.find_all(
                'div', {'class': 'quicklinkSectionItem'})
            for link in linkdata:
                if 'parent' in link.a.attrs['href']:
                    self.advisory_link = '{0}{1}'.format(
                        ROOT, link.a.attrs['href'])
        return self.advisory_link

    def __generate_output(self):
        frmt = '{}{:>30}{}: {}{}'
        wrapper = TextWrapper(width=79, subsequent_indent=(' ' * 32))
        output = frmt.format(GREEN, 'Title', NORMAL, self.title, linesep)
        output += frmt.format(GREEN, 'Year', NORMAL, self.year, linesep)
        output += frmt.format(GREEN, 'Certification', NORMAL,
                              self.certification, linesep)
        synopsis = wrapper.fill(self.synopsis)
        output += frmt.format(GREEN, 'Synopsis', NORMAL, synopsis, linesep)
        try:
            rtg = "{:.0f}%".format(float(self.rating) * 10.0)
            output += frmt.format(GREEN, 'Rating', NORMAL, rtg, linesep)
        except ValueError:
            # We got something we didn't expect.
            pass
        for advisory in self.advisories:
            txt = wrapper.fill(self.advisories[advisory])
            output += frmt.format(GREEN, advisory, NORMAL, txt, linesep)
        return output

    def render(self):
        """Render the data in a shell-presentable format."""
        print(self.__generate_output())

    @property
    def title(self):
        """The title of the movie."""
        if self.__title is None:
            _title = self.raw_data.find('h1', {'class': ''})
            if _title is not None:
                self.__title = _title.text.split('\xa0')[0]
            else:
                self.__title = "[Can't figure out title]"
        return self.__title

    @property
    def certification(self):
        """The certification (rating) of the movie."""
        if self.__certification is None:
            txt_blocks = self.raw_data.find_all('div', {'class': 'txt-block'})
            for block in txt_blocks:
                if 'ertif' in block.text:
                    substrings = block.text.split('\n')
                    if len(substrings) > 2:
                        self.__certification = substrings[2].strip()
        return self.__certification

    @property
    def rating(self):
        """The critical rating of the movie (0.0 to 10.0)."""
        if self.rating_value is None:
            rating_value = self.raw_data.find(
                'span', {'itemprop': 'ratingValue'})
            if rating_value is not None:
                self.rating_value = rating_value.text
            else:
                self.rating_value = "[Can't figure out rating]"
        return self.rating_value

    @property
    def synopsis(self):
        """The synopsis of the movie."""
        if self.__synopsis is None:
            _synopsis = self.raw_data.find('div', {'class': 'summary_text'})
            if _synopsis is not None:
                self.__synopsis = _synopsis.text.strip()
            else:
                self.__synopsis = "[Can't figure out synopsis]"
        return self.__synopsis

    @property
    def year(self):
        """The release year of the movie."""
        if self.__year is None:
            _year = self.raw_data.find('span', {'id': 'titleYear'})
            if _year is not None:
                self.__year = _year.text.strip()
            else:
                self.__year = "[Can't figure out year]"
        return self.__year

    @property
    def advisories(self):
        """A dictionary of parental advisories."""
        _advisories = {}
        if self.__advisories is None:
            self.__get_parental_advisory_link()
            self.advisory_page = request(self.advisory_link)
            sections = self.advisory_page.find_all('section')
            for section in sections:
                if 'id' in section.attrs.keys():
                    if 'advisory' in section.attrs['id']:
                        title = section.find('h4').text
                        adv = section.find_all(
                            'li', attrs={'class': 'ipl-zebra-list__item'})
                        if not adv:
                            self.__advisories = _advisories
                            return self.advisories
                        item = adv[0]
                        _advisories[title] = item.text.replace(
                            'Edit', '').replace('\n', '').strip()
            self.__advisories = _advisories
        return self.__advisories
