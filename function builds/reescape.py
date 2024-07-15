from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import re

string = '56328 BECKER RADIO "EUROPA CASSETTE VOLLSTEREO", LW / MW / SW / USW (FOR TYPE 129 SEE STANDAR'

url = 'http://localhost:5500'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto(url)
        heading = stringHandler(string)
        page.locator(f"h3 > a:has-text('{heading}')").hover()
        page.pause()
        browser.close()

def stringHandler(s):
    strList = s.split('"')
    return strList[0]

main()