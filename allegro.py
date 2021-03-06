import json
import re
from cputable import loadDictionary


def get_auction_data(sockets=['1151', '1150'], price=(0, 150), mobo=False):
    import requests
    TOKEN_URL = 'https://allegro.pl/auth/oauth/token'
    CLIENT_ID = '8c6778c37c404eb88ea01af9758d99cb'
    CLIENT_SECRET = 'IKw91PJBt231MGv8UxU8DkiQrzJ3hTDk89d25ipMYr6vuYnggStludBewJjiB9Xh'

    tokenData = {'grant_type': 'client_credentials'}
    response = requests.post(url=TOKEN_URL, auth=requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET), data=tokenData)

    headers = {
        'charset': 'utf-8',
        'Accept-Language': 'pl-PL',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': "Bearer {}".format(response.json()['access_token'])
    }

    with requests.Session() as session:
        session.headers.update(headers)
        conditionCode = '&offerTypeBuyNow=1&stan=nowe&stan=używane&stan=po zwrocie&stan=powystawowe'
        priceCode = lambda x: f'&price.from={x[0]}&price.to={x[1]}'
        socketCode = ''
        # subbing the + sign and introducing [''] element to put separator in the beginning
        for item in sockets:
            if 'AM' in item:
                socketCode += '&typ-gniazda-procesora=AMD Socket '.join([''] + [re.sub('\+', '%2B', item)])
            elif '115' in item:
                socketCode += '&typ-gniazda-procesora=Intel Socket '.join([''] + [item])
        if mobo:
            URI = 'https://api.allegro.pl/offers/listing?category.id=4228&dodatkowe-elementy=procesor&obslugiwane-procesory=Intel' + conditionCode + priceCode(
                price) + socketCode
        else:
            URI = 'https://api.allegro.pl/offers/listing?category.id=257222' + conditionCode + priceCode(
                price) + socketCode

        i = 0
        auctionList = []
        shift = lambda x: '&offset={0}&limit={1}'.format(x, 100)
        # fetch auction data. Only 100 per GET request
        while True:
            response = session.get(URI + shift(i))
            auctionList.extend(response.json()['items']['promoted'])
            auctionList.extend(response.json()['items']['regular'])
            # availableCount may change during data fetching
            availableCount = response.json()['searchMeta']['availableCount']
            print('Loading page {0} out of {1}'.format(i // 100 + 1, availableCount // 100 + 1))
            if (i + 100) > availableCount: break
            i += 100

    return auctionList


def get_price(element):
    # calculate total price of the product, including delivery cost
    # escaping cases with self-pickup: for some reason its coded differently in json file
    if element['delivery']['availableForFree'] == False:
        try:
            element['sellingMode']['price']['amount'] = str(
                float(element['delivery']['lowestPrice']['amount']) + float(element['sellingMode']['price']['amount']))
        except KeyError:
            pass
    return float(element['sellingMode']['price']['amount'])


def item_link(element):
    return 'https://allegro.pl/oferta/' + element['id']


if __name__ == '__main__':
    
    minBenchmark = 4000
    used_sockets = ['1151', '1150', 'AM3', '1155', '1156', 'AM3+']
    price_range = (0,150)
    cpu_table = loadDictionary('dict.txt', used_sockets)
    
    auctionList = get_auction_data(sockets=used_sockets, price=price_range, mobo=False)
    with open('names.txt', 'w') as outfile:  
        #map(lambda x: outfile.write(x['name']+'\n'), auctionList)
        [outfile.write(element['name']+'\n') for element in auctionList]
        
    #dump read data as json file
    #with open('data.json', 'w') as outfile:  
    #    outfile.write(json.dumps(response.json(), indent=2))
    

    
    buyList = []
    
    pattern = re.compile("([iIgGEXexLlQq]\d*\s*-*\s*\d{3}\d*[PpkKtTsS]*)")
    
    iseries = re.compile('i[3579]\s*-*\s*\d{3,4}[pktcsbehr(hq)(te)(eq)(kf)]*', re.I)
    pentium = re.compile('g\s*\d{3,4}\s*[(te)t]*', re.I)
    xeons   = re.compile('[elx]3*\s*-*\s*\d{4}[lg]*', re.I)
    athlonx = re.compile('x[234p6]\s\d{3,4}[etu\+]*', re.I)
    athlon = re.compile('(?<!fx-)(?<!fx)(?<!\w)(?<!fx\s)(?<!x[234p6]\s)[(le)(gp)(be)]*-*\d{4}[\+eb]*(?!\w)', re.I)
    fxs = re.compile('fx\s*-*\s*b*\d{4}e*', re.I)
    xnbs = re.compile('x[234]\sb\d{2}e*', re.I)
    
    procs = [fxs, athlonx, athlon, xnbs]
    #procs = [iseries, pentium, xeons]
        
       
    for element in auctionList:

        price = get_price(element)
        link = item_link(element)

        link_CPU = lambda name: 'https://www.cpubenchmark.net/cpu.php?cpu=' + re.sub('@', '%40', re.sub(' ', '+', name))
        #[print('{}.{}: \033[0;32m {} \x1b[0m'.format(auctionList.index(element), element['name'], pattern.findall(element['name']), re.I )) for pattern in procs]
        for pattern in procs:
            #---->print('{}.{}: \033[0;32m {} \x1b[0m'.format(auctionList.index(element), element['name'], pattern.findall(element['name']), re.I ))
            
                #break
                
            if pattern.search(element['name'], re.I):
                
                #if motherboards then probably CPU name will be the last identified "G4560"-type key in the name
                if False: #is motherboard 'id=4228&' in URI:
                    newName = pattern.findall(element['name'], re.I)[-1]
                else:
                    newName = pattern.findall(element['name'], re.I)[0]
                
                #print('{0:50.50}: \033[0;32m {1:10.10} {2:10.10} {3:10.10} {4:10.10}\x1b[0m'.format(element['name'], newName, re.sub( '(?<=i[3579])\s(?=\d{3,4})', '-', newName, flags=re.I), re.sub( '(?<=fx)\s(?=\d{3,4})', '-', newName, flags=re.I), re.sub( '(?<![fxi]\w)[\s-]', '', newName, flags=re.I) ))
                #remove whitespaces and insert hyphen for i[357] and fx series     
                newName = re.sub( '(?<=i[3579])\s(?=\d{3,4})', '-', newName, flags=re.I)
                newName = re.sub( '(?<=fx)\s*(?=\d{3,4})', '-', newName, flags=re.I)
                #newName = re.sub( '\s', '', newName)
                newName = re.sub( '(?<![fxi]\w)[\s-]', '', newName, flags=re.I)
                break
            else:
                newName = 'Error'
        #[print('{:50.50}'.format(element['name']), wzor.findall(element['name']), newName) for wzor in procs]
        
        for key in cpu_table:
            #is matching many patterns in findall and search, must change keys to exact names not what is taken from website
            #print(newName, pattern.findall(key))
            if newName.upper() in key.upper():
                buyList.extend([[newName, '{:.2f}'.format(price) +' zl', float(cpu_table[key][0] / price), int(cpu_table[key][0]), link, link_CPU(key)]])
                #print(newName, pattern.findall(key)[0])
        
    
    buyList = sorted(buyList, key=lambda buyList:buyList[2], reverse=True)
    print('total: {0}   matching {2}/{1}'.format(len(auctionList), len(buyList), len(list(filter(lambda x: x[3]>minBenchmark, buyList)))))
    for elem in buyList:
        #pass
        if elem[3]>minBenchmark: print( '{:8.8} \033[0;32m {:>10}\x1b[0m   {:>6.2f} \033[93m{:>5d}\x1b[0m   {}  {}'.format(*elem))
    
        
    
