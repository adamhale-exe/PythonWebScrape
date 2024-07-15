from bs4 import BeautifulSoup
import requests
import pandas as pd

url = 'http://localhost:5500/'
outputCsvName = 'out1.csv'


page = requests.get(url)

soup = BeautifulSoup(page.text, 'html.parser')

tableRows = soup.find('tbody').findChildren('tr', recursive=False)

modelNumber = '123654'

outputList = []

def splitCellsOutputList(i):
    tableCells = i.findChildren('td', recursive=False)
    rowList = [modelNumber]
    for i in tableCells[1:-2]:
        rowList.append(i.get_text().strip().replace('\n',' ').replace('\r', ''))
    outputList.append(rowList)



for i in tableRows:
    try:
        i['style']

        if not 'display: none' in i['style']:
            splitCellsOutputList(i)
    except:
        splitCellsOutputList(i)

dfout = pd.DataFrame(outputList, columns=['Model Number', 'Part Number', 'Description', 'Price','Quantity'])
print(dfout)
dfout.to_csv(outputCsvName, encoding='utf-8-sig')