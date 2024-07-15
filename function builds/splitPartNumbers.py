input='COVER (WASHER)       Replaced by A 201 267 16 76            [002] EXHAUST STOCK OF OLD PART NUMBERS FIRST UP TO IDENT NO A 094336'

def main():
    partNumber = input.split('Replaced by ')[1].split('    ')[0]
    print('' + partNumber)

main()