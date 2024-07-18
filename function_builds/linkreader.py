from bs4 import BeautifulSoup
import requests

url = 'http://localhost:5500/'

page = requests.get(url)

soup = BeautifulSoup(page.text, 'html.parser')

headings = soup.find_all('h3')

for i in headings:
    # Click using this as a match
    page.get_by_text(i.get_text()).click()
    print(i.get_text())
    # Process data on the screen
    # Check if next arrrow available -> repeat
    # Return to headings page and repeate for each heading