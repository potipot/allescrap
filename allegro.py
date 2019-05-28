import requests
import json
import re
from cputable import loadDictionary
import numpy as np

TOKEN_URL = 'https://allegro.pl/auth/oauth/token'
CLIENT_ID = '8c6778c37c404eb88ea01af9758d99cb'
CLIENT_SECRET = 'IKw91PJBt231MGv8UxU8DkiQrzJ3hTDk89d25ipMYr6vuYnggStludBewJjiB9Xh'


def getAccessToken(): 

    tokenData={
        'grant_type': 'client_credentials'
    }
    
    response = requests.post(url = TOKEN_URL,
                             auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
                             data = tokenData)

    return response.json()
    
access_token = getAccessToken()['access_token']

headers = {}
headers['charset'] = 'utf-8'
headers['Accept-Language'] = 'pl-PL'
headers['Content-Type'] = 'application/json'
headers['Accept'] = 'application/vnd.allegro.public.v1+json'
headers['Authorization'] = "Bearer {}".format(access_token)

cpuPrice = (0,150)
minBenchmark = 3500
setPrice = (0,300)

with requests.Session() as session:
    session.headers.update(headers) #&offset=0&limit=&100
    condition = '&offerTypeBuyNow=1&stan=nowe&stan=używane&stan=po zwrocie&stan=powystawowe'
    price = lambda x: '&price.from={0}&price.to={1}'.format(*x)
    #socket = '&{0}1150'.format('typ-gniazda-procesora=Intel Socket ')
    
    #TODO
    #find a better solution for socket filtering using filter() or map()?
    socketsAMD = ['AM3', 'AM2+', 'AM3+']
    sockets = []#['1151', '1156', '1150', '1155']
    k = loadDictionary('dict.txt', socketsAMD)
    
    
    #subbing the + sign and introducing [''] element to put separator in the beginning
    socket = '&typ-gniazda-procesora=AMD Socket '.join(['']+[re.sub('\+', '%2B', x) for x in socketsAMD])
    socket += '&typ-gniazda-procesora=Intel Socket '.join(['']+sockets)
    
    #socket = '&{0}1151&{0}1156&{0}1150&{0}1155&{0}775'.format('typ-gniazda-procesora=Intel Socket ')
    shift = lambda x: '&offset={0}&limit={1}'.format(x,100)
    
    procURI = 'https://api.allegro.pl/offers/listing?category.id=257222'+condition+price(cpuPrice)+socket
    moboURI = 'https://api.allegro.pl/offers/listing?category.id=4228&dodatkowe-elementy=procesor&obslugiwane-procesory=Intel'+condition+price(setPrice)+socket
    URI = procURI
                          
    i=0
    auctionList=[]
    #fetch auction data. Only 100 per GET request
    while True:
        response = session.get(URI+shift(i))
        auctionList.extend(response.json()['items']['promoted'])
        auctionList.extend(response.json()['items']['regular'])
        #availableCount may change during data fetching
        availableCount = response.json()['searchMeta']['availableCount']
        print('Loading page {0} out of {1}'.format(i//100+1,  availableCount//100+1))
        if (i+100)>availableCount: break
        i+=100
    
    #print(auctionList)
    #print('fetched: {0}   inlist: {1}'.format(availableCount, len(auctionList)))
    
    with open('names.txt', 'w') as outfile:  
        #map(lambda x: outfile.write(x['name']+'\n'), auctionList)
        [outfile.write(element['name']+'\n') for element in auctionList]
        
    #dump read data as json file
    with open('data.json', 'w') as outfile:  
        outfile.write(json.dumps(response.json(), indent=2))
    
    
    
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
        
        
        #calculate total price of the product, including delivery cost 
        #escaping cases with self-pickup: for some reason its coded differently in json file
        if element['delivery']['availableForFree'] == False:
            try:
                element['sellingMode']['price']['amount'] = str(float(element['delivery']['lowestPrice']['amount'])+float(element['sellingMode']['price']['amount']))
            except KeyError:
                pass
        price = float(element['sellingMode']['price']['amount'])
        
        #generate links for offer and benchmark
        link = 'https://allegro.pl/oferta/' + element['id']
        linkCPU = lambda name: 'https://www.cpubenchmark.net/cpu.php?cpu=' + re.sub('@', '%40', re.sub(' ', '+', name))
        #[print('{}.{}: \033[0;32m {} \x1b[0m'.format(auctionList.index(element), element['name'], pattern.findall(element['name']), re.I )) for pattern in procs]
        for pattern in procs:
            print('{}.{}: \033[0;32m {} \x1b[0m'.format(auctionList.index(element), element['name'], pattern.findall(element['name']), re.I ))
            
                #break
                
            if pattern.search(element['name'], re.I):
                
                #if motherboards then probably CPU name will be the last identified "G4560"-type key in the name
                if 'id=4228&' in URI:
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
        
        for key in k:
            #is matching many patterns in findall and search, must change keys to exact names not what is taken from website
            #print(newName, pattern.findall(key))
            if newName.upper() in key.upper():
                buyList.extend([[newName, '{:.2f}'.format(price) +' zl', float(k[key][0]/price), int(k[key][0]), link, linkCPU(key)]  ])
                #print(newName, pattern.findall(key)[0])
        
    
    buyList = sorted(buyList, key=lambda buyList:buyList[2], reverse=True)
    print('total: {0}   matching {2}/{1}'.format(availableCount, len(buyList), len(list(filter(lambda x: x[3]>minBenchmark, buyList)))))
    for elem in buyList:
        #pass
        if elem[3]>minBenchmark: print( '{:8.8} \033[0;32m{:>10}\x1b[0m   {:>6.2f} \033[1;31m{:>5d}\x1b[0m   {}  {}'.format(*elem))
    
        
    