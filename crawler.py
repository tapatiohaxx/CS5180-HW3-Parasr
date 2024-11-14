from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient
import ssl

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['cs_department']
pages_collection = db.pages

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class Frontier:
    def __init__(self):
        self.urls = []
        self.visited = set()

    def addURL(self, url):
        if url not in self.visited:
            self.urls.append(url)

    def nextURL(self):
        if self.urls:
            return self.urls.pop(0)
        else:
            return None

    def done(self):
        return len(self.urls) == 0

    def clear(self):
        self.urls = []

    def markVisited(self, url):
        self.visited.add(url)

def retrieveHTML(url):
    try:
        response = urlopen(url, context=ctx)
        if 'text/html' in response.getheader('Content-Type'):
            html = response.read().decode()
            return html
    except Exception as e:
        print(f"Error retrieving {url}: {e}")
    return None

def storePage(url, html):
    if targetPage(html):
        pages_collection.insert_one({'url': url, 'html': html})
        print(f"Stored target page: {url}")
        return True
    return False

def targetPage(html):
    soup = BeautifulSoup(html, 'html.parser')
    h1_tag = soup.find('h1')
    return h1_tag and h1_tag.text == 'Permanent Faculty'

def parse(html, current_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    base_url = urlparse(current_url).scheme + '://' + urlparse(current_url).netloc
    return [urljoin(base_url, link['href']) for link in links]

def crawlerThread(frontier):
    while not frontier.done():
        url = frontier.nextURL()
        if not url:
            break
        if url in frontier.visited:
            continue
        html = retrieveHTML(url)
        if html:
            if storePage(url, html):
                frontier.clear()
                break
            frontier.markVisited(url)
            for link in parse(html, url):
                frontier.addURL(link)

if __name__ == "__main__":
    initial_url = 'https://www.cpp.edu/sci/computer-science/'
    my_frontier = Frontier()
    my_frontier.addURL(initial_url)
    crawlerThread(my_frontier)
