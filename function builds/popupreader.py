from bs4 import BeautifulSoup
import requests

url = 'http://localhost:5500/'

page = requests.get(url)

soup = BeautifulSoup(page.text, 'html.parser')

catalogSoup = soup.find_all('div', {'class': 'dialog-scrollable-section'})

catalogOptions = []

for i in catalogSoup:
    for j in i.findChildren('label'):
        catalogOptions.append(j.get_text())

print(catalogOptions)