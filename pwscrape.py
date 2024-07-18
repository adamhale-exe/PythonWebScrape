"""Imports for regex, html parser, env variables, data manipulation and CSV output, web navigation automation"""
import re
from bs4 import BeautifulSoup
import credentials
import pandas as pd
from playwright.sync_api import sync_playwright

OUTPUT_CSV_NAME = 'out.csv'

def main(modellist, group_number):
    """Command line program to scrape all table data from a list of chassis numbers"""
    error_list = []
    output_list = []

    with sync_playwright() as p:
        # This gets us to the homepage
        page, browser = login_bypass(p)
        page.set_default_timeout(timeout=60000)
        # We now start to iterate through the given model numbers
        for model in modellist:
            try:
                # Initialise the list of catalog options as this is a new model
                catalog_options = []
                # Navigate to and soup the model page
                page.get_by_placeholder('VIN or model code').fill(str(model))
                page.keyboard.press('Enter')
                # Check if a popup had appeared
                if popup_exists(page, 'p:has-text("Please choose a market.")'):
                    page.locator('label:has-text("World")').click()
                    page.keyboard.press('Enter')
                if popup_exists(page, 'p:has-text("Please choose an assortment class.")'):
                    page.locator('label:has-text("Car")').click()
                    page.keyboard.press('Enter')
                if popup_exists(page, 'p:has-text("Please choose a catalogue.")'):
                    ## Find all options and iterate through them
                    catalog_soup = soup_collector(page, 'form > div.dialog-scrollable-section')
                    for i in catalog_soup.findChildren('label'):
                        catalog_options.append(i.get_text())
                    for i in catalog_options:
                        popup_exists(page, 'p:has-text("Please choose a catalogue.")')
                        page.get_by_text(i).click()
                        wait_for_api_call_finished(page, 'div.dialog-buttons > button')
                        print(f'Starting collection for model: {model} variant: {i.strip()}')
                        scrape_all_data(page, model, output_list)
                        page.get_by_placeholder('VIN or model code').fill(str(model))
                        page.keyboard.press('Enter')
                        if popup_exists(page, 'p:has-text("Please choose a market.")'):
                            page.locator('label:has-text("World")').click()
                            page.keyboard.press('Enter')
                        if popup_exists(page, 'p:has-text("Please choose an assortment class.")'):
                            page.locator('label:has-text("Car")').click()
                            page.keyboard.press('Enter')
                    popup_exists(page, 'p:has-text("Please choose a catalogue.")')
                    page.get_by_text(catalog_options[0]).click()
                    wait_for_api_call_finished(page, 'div.dialog-buttons > button')
                    wait_for_api_call_finished(page, 'div > a.home-link:has-text("Mercedes-Benz WebParts")')
                    page.locator('div > h2:has-text("Specify by model")').hover()


                else:
                    print(f'Starting collection for model: {model}')
                    scrape_all_data(page, model, output_list)
                dfout = pd.DataFrame(
                    output_list, columns=['Model Number', 'Category', 'Group', 'Sub-Group', 'Part Number', 'Description', 'Price', 'Quantity']
                    )
                print(dfout)
                dfout.to_csv(f'{group_number}_{model}_{OUTPUT_CSV_NAME}', encoding='utf-8-sig')
            except Exception as err:
                print(f'Error on Model Number: {model}')
                print(f"Unexpected {err=}, {type(err)=}")
                error_list.append([model, err, type(err), err.__cause__])
                dferr = pd.DataFrame(error_list, columns=['Model Number', 'Error text', 'Error type','Error Traceback'])
                dferr.to_csv(f'{group_number}_errors{modellist[-1]}_{OUTPUT_CSV_NAME}', encoding='utf-8-sig')
                browser.close()
        browser.close()
    # Pandas manipulation starts here
    dfout = pd.DataFrame(
        output_list, columns=['Model Number', 'Category', 'Group', 'Sub-Group', 'Part Number', 'Description', 'Price', 'Quantity']
        )
    print(dfout)
    dfout.to_csv(f'{group_number}_final_{modellist[-1]}_{OUTPUT_CSV_NAME}', encoding='utf-8-sig')
    dferr = pd.DataFrame(error_list, columns=['Model Number', 'Error text', 'Error type'])
    dferr.to_csv(f'{group_number}_errors{modellist[-1]}_{OUTPUT_CSV_NAME}', encoding='utf-8-sig')

def login_bypass(p):
    """Function to get through login process"""
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


def scrape_all_data(page, model, output_list):
    """Fucnction to be used when we are on the model page. Will iterate through options and scrape data"""
    check_nav_strip(page, model)
    category_soup = soup_collector(page, 'ul.tab-bar')

    # For each category heading, click it
    for link in category_soup.find_all('a'):
        link = link.get_text()
        wait_for_api_call_finished(page, f'a.tab-bar-link:has-text("{link}")')

        if "(+)" in link:
            option_array = []
            assembly_soup = soup_collector(page, 'select[name="contentPanel:aggregates"]')
            for i in assembly_soup.findChildren('option'):
                option_array.append(i.get_text())
            for index, item in enumerate(option_array[1:]):
                print(f'\tCategory: {link} [{index+1}/{len(option_array[1:])}]\n')
                # Custom wait_for_api_call_finished
                with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
                    page.locator('select[name="contentPanel:aggregates"]').select_option(index=index+1)
                response = response_info.value
                response.finished()
                # Click the OK button
                wait_for_api_call_finished(page, 'div.dialog-buttons > button')
                # Make sure we are on the $link page
                cleaned_link = link.split(" (+)")
                check_nav_strip(page, f'{cleaned_link[0]}:')
                # Iterate through the sidebar collecting data
                main_group_handler(page, model, link, output_list)
                # Return to a known position
                wait_for_api_call_finished(page, f'a:has-text("{link}")')
            # Once all options have been scraped, return to a known position
            page.locator('select[name="contentPanel:aggregates"]').select_option(index=1)
            wait_for_api_call_finished(page, 'div.dialog-buttons > button')
        else:
            print(f'\tCategory: {link}\n')
            if "Paint" in link:
                check_nav_strip(page, link)
            else:
                check_nav_strip(page, f'{link}:')
            main_group_handler(page, model, link, output_list)
    # Return to home to continue scraping
    wait_for_api_call_finished(page, 'div > a.home-link:has-text("Mercedes-Benz WebParts")')
    page.locator('div > h2:has-text("Specify by model")').hover()
    print(f'Completed scrape for Model: { model }')

def nav_to_category_return_groups(page, link):
    """Function to click the category, verify we have arrived and return html object"""
    print (link)
    page.get_by_role("link", name=link, exact=True).click()
    check_nav_strip(page, link)
    return soup_collector(page, 'ul.epc-sub-navi')

def check_nav_strip(page, current_link):
    """Function to verify we arrived on the correct page by checking breadcrumb"""
    current_link = str(current_link)
    if len(current_link) > 20:
        current_link = current_link[:19]
    try:
        page.locator(f'div#bclimiter:has-text("{current_link}")').hover(timeout=5000)
        return True
    except:
        return False

def popup_exists(page, selector):
    """Checkis if a popup is on the page, returns bool"""
    try:
        page.locator('div.dialog').hover(timeout=2500)
        page.locator(selector).hover(timeout=200)
        return True
    except:
        return False

def soup_collector(page, query_selector):
    """Function to return parsed html"""
    page.wait_for_selector(query_selector, timeout=1000)
    html = page.locator(query_selector).inner_html()
    return BeautifulSoup(html, 'html.parser')

def plant_information_handler(page):
    """Function to click and collect information from the PlantInformation link"""
    page.locator('table.order-details-items-table').hover()
    plant_info_list = []
    for i in page.locator('a.link-footnote:has-text("Plantinformation")').all():
        # Click the locator await network finish
        with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
            i.click()
        response = response_info.value
        response.finished()
        # read and parse the popup
        plant_info_popup_handler(page, plant_info_list)
        wait_for_api_call_finished(page, 'div.dialog-buttons > button.next')
    return plant_info_list

def plant_info_popup_handler(page, output_list):
    """Handles the plant info popup"""
    dialog_list = []
    page.wait_for_selector('div.dialog')
    table_data_soup = soup_collector(page, 'div.dialog-scrollable-section > table')
    for row in table_data_soup.find('tbody').findChildren('tr', recursive=False):
        append_to_list(row, dialog_list)
    output_list.append(' | '.join(dialog_list))

def append_to_list(row, output_list):
    """Function to append table data to a list"""
    table_cells = row.findChildren('td', recursive=False)
    for i in table_cells[1:]:
        output_list.append(i.get_text().strip().replace('\n',' '))

def table_handler(page, model, link, group, subgroup, output_list):
    """Function to handle splitting and reading of tables"""
    try:
        table_data_soup = soup_collector(page, 'table.order-details-items-table')
        plant_info_list = 0 #plant_information_handler(page)
        plant_info_counter = [0]
        for row in table_data_soup.find('tbody').findChildren('tr', recursive=False):
            try:
                row['style']

                if not 'display: none' in row['style']:
                    split_cells_output_list(row, model, link, group, subgroup, output_list, plant_info_list, plant_info_counter)
            except:
                split_cells_output_list(row, model, link, group, subgroup, output_list, plant_info_list, plant_info_counter)
    except:
        return False

def split_cells_output_list(row, model_number, link, group, subgroup, output_list, plant_info_list, plant_info_counter):
    """Fucntion takes a table row and parses the cells in that row"""
    table_cells = row.findChildren('td', recursive=False)
    row_list = [model_number, link, group, subgroup]
    starting_col = 1
    if link == "Paint & Operating fluids":
        starting_col = 0
    for i in table_cells[starting_col:-2]:
        row_list.append(i.get_text().strip().replace('\n',' ').replace('\r', ''))
#    if 'Plantinformation' in row_list[5]:
#        row_list.append(plant_info_list[plant_info_counter[0]])
#        plant_info_counter[0] += 1
#    else:
#        row_list.append("-")
#    if 'Replaced by' in row_list[5]:
#        row_list.append(row_list[5].split('Replaced by ')[1].split('    ')[0])
#    else:
#        row_list.append("-")
    output_list.append(row_list)

def collection_handler(page, model, link, group, subgroup, output_list):
    """Handles pagination when scraping data with pages"""
    while page.locator('span.pagination-next').get_attribute('class') == 'pagination-next enabled':
        table_handler(page, model, link, group, subgroup, output_list)
        try:
            wait_for_api_call_finished(page, 'span.pagination-next')
        except:
            print('Unable to find api call, continuing')
    table_handler(page, model, link, group, subgroup, output_list)

def data_collection(page, model, link, group, subgroup, output_list):
    """Checks if category had pagination and decides how to proceed"""
    pagination_soup = soup_collector(page, 'div.epc-content')
    if pagination_soup.find('span', { 'class':'pagination-next' }):
        collection_handler(page, model, link, group, subgroup, output_list)
    else:
        table_handler(page, model, link, group, subgroup, output_list)

def find_and_click(page, locator):
    """Clicks using the locator"""
    page.locator(locator).click()

def wait_for_api_call_finished(page, locator):
    """Clicks and waits for html to be downloaded before proceeding"""
    try:
        page.wait_for_selector(locator)
        with page.expect_response(re.compile(r'^.*webparts\/ng\/customer\/epc\/main.*$')) as response_info:
            find_and_click(page, locator)
        response = response_info.value
        response.finished()
    except:
        print(f"Response either not found or never finished at: {locator}")

def string_handler(s):
    """Splits the string on a problematic character and returns the first part"""
    str_list = s.split('"')
    return str_list[0]

def main_group_handler(page, model, link, output_list):
    """Handles navigating the sidebar and collecting data"""
    main_group_soup = soup_collector(page, 'ul.epc-sub-navi')
        # If we can see the slider/carousel
    if page.is_visible('div.part-detection-slider-container'):
        # We are already at a stage that we can start to take the data out and store it
        current_group = main_group_soup.find_all('a')[2]
        try:
            subgroup = str(page.locator('div.collapse-wrapper > h1').inner_text(timeout=500))
        except:
            subgroup = current_group
        # Check for pagination
        data_collection(page, model, link, current_group, subgroup, output_list)

    else:
    # For each group, click it
        for index, group in enumerate(main_group_soup.find_all('a')[2:]):
            progressBar(index + 1, len(main_group_soup.find_all('a')[2:]))
            current_group = group.get_text()
            wait_for_api_call_finished(page, f'a.epc-sub-navi-item:has-text("{current_group}")')
            check_nav_strip(page, current_group)
            if page.is_visible('div.part-detection-slider-container'):
                # We are already at a stage that we can start to take the data out and store it
                try:
                    subgroup = str(page.locator('div.collapse-wrapper > h1').inner_text(timeout=500))
                except:
                    subgroup = current_group
                # Check for pagination
                data_collection(page, model, link, current_group, subgroup, output_list)
            elif link == "Paint & Operating fluids":
                # We are already at a stage that we can start to take the data out and store it
                subgroup = current_group
                data_collection(page, model, link, current_group, subgroup, output_list)
            else:
                # Find headings for each image category
                subgroup_soup = soup_collector(page, 'div.epc-content')
                headings = subgroup_soup.find_all('h3')
                for i in headings:
                    heading = string_handler(i.get_text())
                    wait_for_api_call_finished(page, f'h3 > a:has-text("{heading}")')
                    data_collection(page, model, link, current_group, heading, output_list)
                    wait_for_api_call_finished(page, f'a.epc-sub-navi-item:has-text("{current_group}")')

def progress_bar(progress, total):
    """Displays a progress bar in the terminal"""
    percent = 100 * (progress / float(total))
    current_bar = '█' * int(percent) + '-' * (100 - int(percent))
    if progress < total:
        print(f'\r\t\t|{current_bar}| {percent:.2f}%', end="\r")
    else:
        print(f'\r\t\t\033[92m|{current_bar}| {percent:.2f}%', end="\n\n\033[37m")

try:
    main(
        [120010,120110,121010,121110,121040,121042,180010,180030,180037],
        'Grp1')
except:
    print('Continuing to next run')
try:
    main(
        [198040,198043,198042,128010,128030,128037,111010,111012,111014,111021,111024,111026,111023,111025,111027,112014,112015,112021,112023],
        'Grp2')
except:
    print('Continuing to next run')
try:
    main(
        [110010,110011,110110,113042,113043,113044,100012,100014,100615,100016,100617,108012,108014,108015,108016,108018,108019,108057,108058,108067],
        'Grp3')
except:
    print('Continuing to next run')
try:
    main(
        [108068,109015,109016,109018,109056,109057,115015,115010,115017,115110,115114,115115,115117,114010,114011,114015,114060,114062,114021,114023],
        'Grp4')
except:
    print('Continuing to next run')
try:
    main(
        [114022,114073,114072,107042,107043,107044,107045,107046,107041,107047,107048,107022,107023,107024,107026,107025,116020,116024,116025,116028],
        'Grp5')
except:
    print('Continuing to next run')
try:
    main(
        [116029,116032,116033,116036,116120,123020,123220,123023,123223,123026,123030,123033,123120,123126,123123,123130,123133,123043,123243,123050],
        'Grp6')
except:
    print('Continuing to next run')
try:
    main(
        [123053,123150,123153,123280,123083,123283,123086,123093,123183,123190,123193,126020,126021,126022,126023,126024,126025,126032,126033,126034],
        'Grp7')
except:
    print('Continuing to next run')
try:
    main(
        [126035,126036,126037,126038,126039,126120,126125,126134,126135,126043,126044,126045,126046,460210,460212,460216,460218,460220,460221,460222],
        'Grp8')
except:
    print('Continuing to next run')
try:
    main(
        [406223,460224,460227,460228,460229,460230,460231,460232,460233,460236,460237,460238,460239,460241,460243,460249,460310,460312,460317,460320],
        'Grp9')
except:
    print('Continuing to next run')
try:
    main(
        [460321,460322,460323,460325,460328,460329,460330,460331,460332,460333,460337,460338,460341,460343,201022,201023,201024,201028,201034,201035],
        'Grp10')
except:
    print('Continuing to next run')
try:
    main(
        [201036,201029,201018,201122,201126,201128,124020,124121,124019,124023,124022,124026,124226,124028,124030,124230,124031,124032,124034,124036],
        'Grp11')
except:
    print('Continuing to next run')
try:
    main(
        [124120,124125,124126,124129,124130,124131,124330,124133,124333,124040,124043,124042,124050,124051,124052,124060,124062,124061,124066,124080],
        'Grp12')
except:
    print('Continuing to next run')
try:
    main(
        [124081,124079,124083,124082,124088,124090,124290,124091,124092,124180,124185,124186,124188,124190,124191,124193,124393,129060,129061,129059],
        'Grp13')
except:
    print('Continuing to next run')
try:
    main(
        [129058,129063,129064,129066,129067,129068,129076,140028,140032,140033,140042,140043,140050,140051,140056,140057,140134,140136,140063,140070],
        'Grp14')
except:
    print('Continuing to next run')
try:
    main(
        [140076,202018,202020,202025,202022,202023,202024,202026,202028,202029,202033,202120,202122,202134,202121,202133,202125,202128,202078,202081],
        'Grp15')
except:
    print('Continuing to next run')
try:
    main(
        [202080,202082,202087,202083,202085,202086,202088,202089,202093,202180,202194,202182,202193,202188,170435,170445,170447,170444,170449,170465],
         'Grp16')
except:
    print('Continuing to next run')
try:
    main(
        [170466,208335,208435,208345,208344,208445,208444,208347,208348,208447,208448,208365,208465,208370,208470,208374,208474],
        'Grp17')
except:
    print('Continuing to next run')
