from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

url = 'http://localhost:5500/function%20builds/'

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto(url)
        plantList = plantInformationHandler(page)
        print(plantList)


def plantInformationHandler(page):
    page.locator('table.order-details-items-table').hover()
    plantInfoList = []
    for i in page.locator('a.link-footnote:has-text("Plantinformation")').all():
        # Click the locator await network finish
        with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
                i.click()
        response = response_info.value
        response.finished()
        # read and parse the popup
        popupHandler(page, plantInfoList)
        page.pause()
    return plantInfoList

def popupHandler(page, outputList):
    dialogList = []
    page.wait_for_selector('div.dialog')
    tableDataSoup = soupCollector(page, 'div.dialog-scrollable-section > table')
    for row in tableDataSoup.find('tbody').findChildren('tr', recursive=False):
        appendToList(row, dialogList)  
    outputList.append(dialogList)


def appendToList(row, list):
    tableCells = row.findChildren('td', recursive=False)
    for i in tableCells[1:]:
         list.append(i.get_text().strip())

def waitForAPICallFinished(page, locator):
    try:
        page.wait_for_selector(locator)
        with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
                findAndClick(page, locator)
        response = response_info.value
        response.finished()
    except:
        print(f"Response either not found or never finished at: {locator}")

def findAndClick(page, locator):
    page.locator(locator).click()

def soupCollector(page, querySelector):
    page.wait_for_selector(querySelector, timeout=1000)
    html = page.locator(querySelector).inner_html()
    return BeautifulSoup(html, 'html.parser')
main()