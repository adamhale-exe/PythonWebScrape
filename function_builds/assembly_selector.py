"""Module to automate user actions."""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = 'http://localhost:5500'

def assembly_selector():
    """Module to build and test a function that deals with a popup."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto(URL)

        html = page.query_selector('select[name="contentPanel:aggregates"]').inner_html()
        soup = BeautifulSoup(html, 'html.parser')

        option_array = []

        for i in soup.findChildren('option'):
            option_array.append(i.get_text())
            print(i.get_text)
        print(option_array)
        for index, item in enumerate(option_array[1:]):
            print(index+1)
            page.locator('select[name="contentPanel:aggregates"]').select_option(index=index+1)
            page.pause()
        browser.close()

assembly_selector()
