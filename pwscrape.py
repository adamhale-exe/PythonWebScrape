from bs4 import BeautifulSoup
import credentials
import pandas as pd
from playwright.sync_api import sync_playwright
import re

outputCSVName = 'out.csv'

def main(modellist, groupNumber):

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
                    for i in catalogOptions:
                        popupExists(page, 'p:has-text("Please choose a catalogue.")')
                        page.get_by_text(i).click()
                        waitForAPICallFinished(page, 'div.dialog-buttons > button')
                        print(f'Starting collection for model: {model} variant: {i.strip()}')
                        scrapeAllData(page, model, outputList)
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
                dfout = pd.DataFrame(outputList, columns=['Model Number', 'Category', 'Group', 'Sub-Group', 'Part Number', 'Description', 'Price', 'Quantity'])
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
    # Pandas manipulation starts here
    dfout = pd.DataFrame(outputList, columns=['Model Number', 'Category', 'Group', 'Sub-Group', 'Part Number', 'Description', 'Price', 'Quantity'])
    print(dfout)
    dfout.to_csv(f'{groupNumber}_final_{modellist[-1]}_{outputCSVName}', encoding='utf-8-sig')
    dferr = pd.DataFrame(errorList, columns=['Model Number', 'Error text', 'Error type'])
    dferr.to_csv(f'{groupNumber}_errors{modellist[-1]}_{outputCSVName}', encoding='utf-8-sig')

def loginBypass(p):
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(credentials.loginurl)
    page.fill('input#userid', credentials.username)
    page.click('button#next-btn')
    page.fill('input#password', credentials.password)
    page.click('button#loginSubmitButton')
    page.get_by_text('Accept all').click()
    page.get_by_text('MB WebParts').hover()
    page.goto(credentials.homeurl)
    page.get_by_test_id('uc-accept-all-button').click()
    page.get_by_text(credentials.locationdivision).click()
    page.get_by_text('Apply').click()
    page.get_by_text(credentials.locationsubdivision).click()
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
                print(f'\tCategory: {link} [{index+1}/{len(optionArray[1:])}]\n')
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
            print(f'\tCategory: {link}\n')
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
        waitForAPICallFinished(page, 'div.dialog-buttons > button.next')
    return plantInfoList

def popupHandler(page, outputList):
    dialogList = []
    page.wait_for_selector('div.dialog')
    tableDataSoup = soupCollector(page, 'div.dialog-scrollable-section > table')
    for row in tableDataSoup.find('tbody').findChildren('tr', recursive=False):
        appendToList(row, dialogList)  
    outputList.append(' | '.join(dialogList))

def appendToList(row, list):
    tableCells = row.findChildren('td', recursive=False)
    for i in tableCells[1:]:
         list.append(i.get_text().strip().replace('\n',' '))

def tableHandler(page, model, link, group, subgroup, outputList):
    try:
        tableDataSoup = soupCollector(page, 'table.order-details-items-table')
        plantInfoList = 0 #plantInformationHandler(page)
        plantInfoCounter = [0]
        for row in tableDataSoup.find('tbody').findChildren('tr', recursive=False):
            try:
                row['style']

                if not 'display: none' in row['style']:
                    splitCellsOutputList(row, model, link, group, subgroup, outputList, plantInfoList, plantInfoCounter)
            except:
                splitCellsOutputList(row, model, link, group, subgroup, outputList, plantInfoList, plantInfoCounter)
    except:
        return False

def splitCellsOutputList(row, modelNumber, link, group, subgroup, outputList, plantInfoList, plantInfoCounter):
    tableCells = row.findChildren('td', recursive=False)
    rowList = [modelNumber, link, group, subgroup]
    startingCol = 1
    if link == "Paint & Operating fluids":
        startingCol = 0
    for i in tableCells[startingCol:-2]:
        rowList.append(i.get_text().strip().replace('\n',' ').replace('\r', ''))
#    if 'Plantinformation' in rowList[5]:
#        rowList.append(plantInfoList[plantInfoCounter[0]])
#        plantInfoCounter[0] += 1
#    else:
#        rowList.append("-")
#    if 'Replaced by' in rowList[5]:
#        rowList.append(rowList[5].split('Replaced by ')[1].split('    ')[0])
#    else:
#        rowList.append("-")
    outputList.append(rowList)

def collectionHandler(page, model, link, group, subgroup, outputList):
    while page.locator('span.pagination-next').get_attribute('class') == 'pagination-next enabled':
        tableHandler(page, model, link, group, subgroup, outputList)
        try:
            waitForAPICallFinished(page, 'span.pagination-next')
        except:
            print('Unable to find api call, continuing')
    tableHandler(page, model, link, group, subgroup, outputList)

def dataCollection(page, model, link, group, subgroup, outputList):
    paginationSoup = soupCollector(page, 'div.epc-content')
    if paginationSoup.find('span', { 'class':'pagination-next' }):
        collectionHandler(page, model, link, group, subgroup, outputList)
    else:
        tableHandler(page, model, link, group, subgroup, outputList)       

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
        currentGroup = mainGroupSoup.find_all('a')[2]
        try:
            subgroup = str(page.locator('div.collapse-wrapper > h1').inner_text(timeout=500))
        except:
            subgroup = currentGroup
        # Check for pagination
        dataCollection(page, model, link, currentGroup, subgroup, outputList)

    else:
    # For each group, click it
        for index, group in enumerate(mainGroupSoup.find_all('a')[2:]):
            progressBar(index + 1, len(mainGroupSoup.find_all('a')[2:]))
            currentGroup = group.get_text()
            waitForAPICallFinished(page, f'a.epc-sub-navi-item:has-text("{currentGroup}")')
            checkNavStrip(page, currentGroup)
            if page.is_visible('div.part-detection-slider-container'):
                # We are already at a stage that we can start to take the data out and store it
                try:
                    subgroup = str(page.locator('div.collapse-wrapper > h1').inner_text(timeout=500))
                except:
                    subgroup = currentGroup
                # Check for pagination
                dataCollection(page, model, link, currentGroup, subgroup, outputList)
            elif link == "Paint & Operating fluids":
                # We are already at a stage that we can start to take the data out and store it
                subgroup = currentGroup
                dataCollection(page, model, link, currentGroup, subgroup, outputList)
            else:
                # Find headings for each image category
                subgroupSoup = soupCollector(page, 'div.epc-content')
                headings = subgroupSoup.find_all('h3')
                for i in headings:
                    heading = stringHandler(i.get_text())
                    waitForAPICallFinished(page, f'h3 > a:has-text("{heading}")')
                    dataCollection(page, model, link, currentGroup, heading, outputList)
                    waitForAPICallFinished(page, f'a.epc-sub-navi-item:has-text("{currentGroup}")')

def progressBar(progress, total):
    percent = 100 * (progress / float(total))
    bar = '█' * int(percent) + '-' * (100 - int(percent))
    if progress < total:
        print(f'\r\t\t|{bar}| {percent:.2f}%', end="\r")
    else:
        print(f'\r\t\t\033[92m|{bar}| {percent:.2f}%', end="\n\n\033[37m")

try:
    main([120010,120110,121010,121110,121040,121042,180010,180030,180037],'Grp1')
except:
    print('Continuing to next run')
try:
    main([198040,198043,198042,128010,128030,128037,111010,111012,111014,111021,111024,111026,111023,111025,111027,112014,112015,112021,112023],'Grp2')
except:
    print('Continuing to next run')
try:
    main([110010,110011,110110,113042,113043,113044,100012,100014,100615,100016,100617,108012,108014,108015,108016,108018,108019,108057,108058,108067],'Grp3')
except:
    print('Continuing to next run')
try:
    main([108068,109015,109016,109018,109056,109057,115015,115010,115017,115110,115114,115115,115117,114010,114011,114015,114060,114062,114021,114023],'Grp4')
except:
    print('Continuing to next run')
try:
    main([114022,114073,114072,107042,107043,107044,107045,107046,107041,107047,107048,107022,107023,107024,107026,107025,116020,116024,116025,116028],'Grp5')
except:
    print('Continuing to next run')
try:
    main([116029,116032,116033,116036,116120,123020,123220,123023,123223,123026,123030,123033,123120,123126,123123,123130,123133,123043,123243,123050],'Grp6')
except:
    print('Continuing to next run')
try:
    main([123053,123150,123153,123280,123083,123283,123086,123093,123183,123190,123193,126020,126021,126022,126023,126024,126025,126032,126033,126034],'Grp7')
except:
    print('Continuing to next run')
try:
    main([126035,126036,126037,126038,126039,126120,126125,126134,126135,126043,126044,126045,126046,460210,460212,460216,460218,460220,460221,460222],'Grp8')
except:
    print('Continuing to next run')
try:
    main([406223,460224,460227,460228,460229,460230,460231,460232,460233,460236,460237,460238,460239,460241,460243,460249,460310,460312,460317,460320],'Grp9')
except:
    print('Continuing to next run')
try:
    main([460321,460322,460323,460325,460328,460329,460330,460331,460332,460333,460337,460338,460341,460343,201022,201023,201024,201028,201034,201035],'Grp10')
except:
    print('Continuing to next run')
try:
    main([201036,201029,201018,201122,201126,201128,124020,124121,124019,124023,124022,124026,124226,124028,124030,124230,124031,124032,124034,124036],'Grp11')
except:
    print('Continuing to next run')
try:
    main([124120,124125,124126,124129,124130,124131,124330,124133,124333,124040,124043,124042,124050,124051,124052,124060,124062,124061,124066,124080],'Grp12')
except:
    print('Continuing to next run')
try:
    main([124081,124079,124083,124082,124088,124090,124290,124091,124092,124180,124185,124186,124188,124190,124191,124193,124393,129060,129061,129059],'Grp13')
except:
    print('Continuing to next run')
try:
    main([129058,129063,129064,129066,129067,129068,129076,140028,140032,140033,140042,140043,140050,140051,140056,140057,140134,140136,140063,140070],'Grp14')
except:
    print('Continuing to next run')
try:
    main([140076,202018,202020,202025,202022,202023,202024,202026,202028,202029,202033,202120,202122,202134,202121,202133,202125,202128,202078,202081],'Grp15')
except:
    print('Continuing to next run')
try:
    main([202080,202082,202087,202083,202085,202086,202088,202089,202093,202180,202194,202182,202193,202188,170435,170445,170447,170444,170449,170465],'Grp16')
except:
    print('Continuing to next run')
try:
    main([170466,208335,208435,208345,208344,208445,208444,208347,208348,208447,208448,208365,208465,208370,208470,208374,208474],'Grp17')
except:
    print('Continuing to next run')