from bs4 import BeautifulSoup
import credentials
import pandas as pd
from playwright.sync_api import sync_playwright
import re

outputCSVName = 'out.csv'

def main(modellist, groupNumber, catalogCollectionStart =0, catalogCollectionEnd =None):

    

    errorList = []
    outputList = []

    with sync_playwright() as p:
        # This gets us to the homepage
        page, browser = loginBypass(p)
        page.set_default_timeout(timeout=60000)
        # We now start to iterate through the given model numbers
        for model in modellist:
            try:
                # Initialise the list of catalog options as this is a new model
                catalogOptions = []
                # Navigate to and soup the model page
                page.get_by_placeholder('VIN or model code').fill(str(model))
                page.keyboard.press('Enter')
                # Check if a popup had appeared
                if popupExists(page, 'p:has-text("Please choose a market.")'):
                    page.locator('label:has-text("World")').click()
                    page.keyboard.press('Enter')
                if popupExists(page, 'p:has-text("Please choose an assortment class.")'):
                    page.locator('label:has-text("Car")').click()
                    page.keyboard.press('Enter')
                if popupExists(page, 'p:has-text("Please choose a catalogue.")'):
                    ## Find all options and iterate through them
                    catalogSoup = soupCollector(page, 'form > div.dialog-scrollable-section')
                    for i in catalogSoup.findChildren('label'):
                        catalogOptions.append(i.get_text())
                    for i in catalogOptions[catalogCollectionStart:catalogCollectionEnd]:
                        index = catalogOptions.index(i)
                        popupExists(page, 'p:has-text("Please choose a catalogue.")')
                        page.get_by_text(i).click()
                        waitForAPICallFinished(page, 'div.dialog-buttons > button')
                        print(f'Starting collection for model: {model} variant: {i.strip()}')
                        scrapeAllData(page, model, outputList)
                        # Output to CSV once one full scrape
                        dfout = pd.DataFrame(outputList, columns=['Model Number', 'Category', 'Group', 'Part Number', 'Description', 'Price','Quantity'])
                        print(dfout)
                        dfout.to_csv(f'{groupNumber}_{model}_{index}_{outputCSVName}', encoding='utf-8-sig')
                        page.get_by_placeholder('VIN or model code').fill(str(model))
                        page.keyboard.press('Enter')
                        if popupExists(page, 'p:has-text("Please choose a market.")'):
                            page.locator('label:has-text("World")').click()
                            page.keyboard.press('Enter')
                        if popupExists(page, 'p:has-text("Please choose an assortment class.")'):
                            page.locator('label:has-text("Car")').click()
                            page.keyboard.press('Enter')
                    popupExists(page, 'p:has-text("Please choose a catalogue.")')
                    page.get_by_text(catalogOptions[0]).click()
                    waitForAPICallFinished(page, 'div.dialog-buttons > button')
                    waitForAPICallFinished(page, f'div > a.home-link:has-text("Mercedes-Benz WebParts")')
                    page.locator('div > h2:has-text("Specify by model")').hover()


                else:
                    print(f'Starting collection for model: {model}')
                    scrapeAllData(page, model, outputList)
                dfout = pd.DataFrame(outputList, columns=['Model Number', 'Category', 'Group', 'Part Number', 'Description', 'Price','Quantity'])
                print(dfout)
                dfout.to_csv(f'{groupNumber}_{model}_{outputCSVName}', encoding='utf-8-sig')
            except Exception as err:
                print(f'Error on Model Number: {model}')
                print(f"Unexpected {err=}, {type(err)=}")
                errorList.append([model, err, type(err), err.__cause__])
                dferr = pd.DataFrame(errorList, columns=['Model Number', 'Error text', 'Error type','Error Traceback'])
                dferr.to_csv(f'{groupNumber}_errors{modellist[-1]}_{outputCSVName}', encoding='utf-8-sig')
                browser.close()
        browser.close()
    # Pandas manipulation would start here
    dfout = pd.DataFrame(outputList, columns=['Model Number', 'Category', 'Group', 'Part Number', 'Description', 'Price','Quantity'])
    print(dfout)
    dfout.to_csv(f'{groupNumber}_final_{modellist[-1]}_{outputCSVName}', encoding='utf-8-sig')
    dferr = pd.DataFrame(errorList, columns=['Model Number', 'Error text', 'Error type'])
    dferr.to_csv(f'{groupNumber}_errors{modellist[-1]}_{outputCSVName}', encoding='utf-8-sig')

def loginBypass(p):
    browser = p.chromium.launch(headless=False, slow_mo=50)
    page = browser.new_page()
    page.goto('https://aftersales.mercedes-benz.com/home/')
    page.fill('input#userid', credentials.username)
    page.click('button#next-btn')
    page.fill('input#password', credentials.password)
    page.click('button#loginSubmitButton')
    page.get_by_text('Accept all').click()
    page.get_by_text('MB WebParts').hover()
    page.goto('https://webparts.mercedes-benz.com/webparts')
    page.get_by_test_id('uc-accept-all-button').click()
    page.get_by_text('537-779-01 - Drayton Group Limited (Hindlip Lane, WR3 8SB, Worcester)').click()
    page.get_by_text('Apply').click()
    page.get_by_text('The SL Shop Ltd (Drayton Manor Drive, CV37 9RQ Stratford Upon Avon) - C-Outlet.XY03711861 ( B1131 )').click()
    page.get_by_text('Apply').click()
    try:
        page.get_by_text("Shopping cart notice").hover(timeout=10000) 
        page.get_by_role("button", name="Clear cart", exact=True).click()
    except:
        print('No previous cart found')
    return page, browser


def scrapeAllData(page, model, outputList):
    checkNavStrip(page, model)
    categorySoup = soupCollector(page, 'ul.tab-bar')

    # For each category heading, click it
    for link in categorySoup.find_all('a'):
        link = link.get_text()
        waitForAPICallFinished(page, f'a.tab-bar-link:has-text("{link}")')

        if "(+)" in link:
            optionArray = []
            assemblySoup = soupCollector(page, 'select[name="contentPanel:aggregates"]')
            for i in assemblySoup.findChildren('option'):
                optionArray.append(i.get_text())
            for index, item in enumerate(optionArray[1:]):
                print(f'\tCategory: {link} [{index+1}/{len(optionArray[1:])}]')
                with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
                    page.locator('select[name="contentPanel:aggregates"]').select_option(index=index+1)
                response = response_info.value
                response.finished()
                waitForAPICallFinished(page, 'div.dialog-buttons > button')
                cleanedLink = link.split(" (+)")
                checkNavStrip(page, f'{cleanedLink[0]}:')
                mainGroupHandler(page, model, link, outputList)
                waitForAPICallFinished(page, f'a:has-text("{link}")')
            page.locator('select[name="contentPanel:aggregates"]').select_option(index=1)
            waitForAPICallFinished(page, 'div.dialog-buttons > button')
        else:
            print(f'\tCategory: {link}')
            if "Paint" in link:
                checkNavStrip(page, link)
            else:
                checkNavStrip(page, f'{link}:')
            mainGroupHandler(page, model, link, outputList)
    # Return to home to continue scraping
    waitForAPICallFinished(page, f'div > a.home-link:has-text("Mercedes-Benz WebParts")')
    page.locator('div > h2:has-text("Specify by model")').hover()
    print(f'Completed scrape for Model: { model }')

def navToCategoryReturnGroups(page, link):
    print (link)
    page.get_by_role("link", name=link, exact=True).click()
    checkNavStrip(page, link)
    return soupCollector(page, 'ul.epc-sub-navi')

def checkNavStrip(page, currentLink):
    currentLink = str(currentLink)
    if len(currentLink) > 20:
        currentLink = currentLink[:19]
    try:
        page.locator(f'div#bclimiter:has-text("{currentLink}")').hover(timeout=5000)
        return True
    except:
        return False
    
def popupExists(page, selector):
    try:
        page.locator('div.dialog').hover(timeout=2500)
        page.locator(selector).hover(timeout=200)
        return True
    except:
        return False

def soupCollector(page, querySelector):
    page.wait_for_selector(querySelector, timeout=1000)
    html = page.locator(querySelector).inner_html()
    return BeautifulSoup(html, 'html.parser')

def tableHandler(page, model, link, group, outputList):
    try:
        tableDataSoup = soupCollector(page, 'table.order-details-items-table')
        for row in tableDataSoup.find('tbody').findChildren('tr', recursive=False):
            try:
                row['style']

                if not 'display: none' in row['style']:
                    splitCellsOutputList(row, model, link, group, outputList)
            except:
                splitCellsOutputList(row, model, link, group, outputList)
    except:
        return False

def splitCellsOutputList(i, modelNumber, link, group, outputList):
    tableCells = i.findChildren('td', recursive=False)
    rowList = [modelNumber, link, group]
    startingCol = 1
    if link == "Paint & Operating fluids":
        startingCol = 0
    for i in tableCells[startingCol:-2]:
        rowList.append(i.get_text().strip().replace('\n',' ').replace('\r', ''))
    outputList.append(rowList)

def collectionHandler(page, model, link, group, outputList):
    while page.locator('span.pagination-next').get_attribute('class') == 'pagination-next enabled':
        tableHandler(page, model, link, group, outputList)
        try:
            waitForAPICallFinished(page, 'span.pagination-next')
        except:
            print('Unable to find api call, continuing')
    tableHandler(page, model, link, group, outputList)

def dataCollection(page, model, link, group, outputList):
    paginationSoup = soupCollector(page, 'div.epc-content')
    if paginationSoup.find('span', { 'class':'pagination-next' }):
        collectionHandler(page, model, link, group, outputList)
    else:
        tableHandler(page, model, link, group, outputList)       

def findAndClick(page, locator):
    page.locator(locator).click()

def waitForAPICallFinished(page, locator):
    try:
        page.wait_for_selector(locator)
        with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
                findAndClick(page, locator)
        response = response_info.value
        response.finished()
    except:
        print(f"Response either not found or never finished at: {locator}")


def stringHandler(s):
    strList = s.split('"')
    return strList[0]

def mainGroupHandler(page, model, link, outputList):
    mainGroupSoup = soupCollector(page, 'ul.epc-sub-navi')
        # If we can see the slider/carousel
    if page.is_visible('div.part-detection-slider-container'):
        # We are already at a stage that we can start to take the data out and store it
        # Check for pagination
        dataCollection(page, model, link, link, outputList)

    else:
    # For each group, click it
        for group in mainGroupSoup.find_all('a')[2:]:
            currentGroup = group.get_text()
            waitForAPICallFinished(page, f'a.epc-sub-navi-item:has-text("{currentGroup}")')
            checkNavStrip(page, currentGroup)
            if page.is_visible('div.part-detection-slider-container') or link == "Paint & Operating fluids":
                # We are already at a stage that we can start to take the data out and store it
                # Check for pagination
                dataCollection(page, model, link, currentGroup, outputList)
            else:
                # Find headings for each image category
                subgroupSoup = soupCollector(page, 'div.epc-content')
                headings = subgroupSoup.find_all('h3')
                for i in headings:
                    heading = stringHandler(i.get_text())
                    waitForAPICallFinished(page, f'h3 > a:has-text("{heading}")')
                    dataCollection(page, model, link, currentGroup, outputList)
                    waitForAPICallFinished(page, f'a.epc-sub-navi-item:has-text("{currentGroup}")')


try:
    main([124290,124021],'ErrorGroup')
except:
    print('Continuing to next run')

