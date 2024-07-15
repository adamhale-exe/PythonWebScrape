from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = 'http://localhost:5500'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        html = page.query_selector('div.epc-content').inner_html()
        soup = BeautifulSoup(html, 'html.parser')

        # found = soup.find('span', { 'class':'pagination-next' })
        if soup.find('span', { 'class':'pagination-next' }):
            print('Run collectionHandler')
        else:
            print('No pagination, run tableHandler')
        browser.close()

main()