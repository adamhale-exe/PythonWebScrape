from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = 'http://localhost:5500'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto(url)

        html = page.query_selector('select[name="contentPanel:aggregates"]').inner_html()
        soup = BeautifulSoup(html, 'html.parser')

        optionArray = []

        for i in soup.findChildren('option'):
            optionArray.append(i.get_text())
            print(i.get_text)
        
        print(optionArray)
        for index, item in enumerate(optionArray[1:]):
            print(index+1)
            page.locator('select[name="contentPanel:aggregates"]').select_option(index=index+1)
            page.pause()
        browser.close()

main()