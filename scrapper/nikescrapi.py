import requests         
import json
import pandas as pd
import numpy as np
import os
import shutil

from tqdm import tqdm
from bs4 import BeautifulSoup  
from datetime import datetime

class NikeScrAPI:   
    '''
    Uses nike's website API to scrape data.
        NOTE: for production set max_pages = 200
    '''
    def __init__(
        self,
        country='US', 
        lan='en',
        max_pages=1, 
        get_description=True, 
        single_category=None, 
        debug=False, 
        filename='nike',
        path='data'
    ):
        
        self.__count = 24
        self.__page_size = 24
        self.__country = country
        self.__lan = lan
        self.__DEBUG = debug
        self.__url_base = "https://www.nike.com" 
        self.__DEFAULT_REQUESTS_TIMEOUT = (5, 15) # for example
        self.__filePrefix = filename
        self.__path = path
        
        # If TRUE, then it gets the full description and ratings from each product's url. 
        # Takes more time, but data is complet
        self.__full_description = get_description
        
        # Estimated max number of pages in each category
        self.__max_number_of_pages = max_pages  # recommended 200 for production, 1 for testing
        
        # Data Structure
        self.shoeDict = { 
            'UID':[],
            'cloudProdID':[],
            'productID':[],
            'shortID':[],
            'colorNum':[],
            'title':[],
            'subtitle':[],
            'category':[],
            'type':[],
            'currency':[],
            'fullPrice':[],
            'currentPrice':[],
            'sale':[],
            'TopColor':[],
            'channel':[],
            'short_description':[],
            'rating':[],
            
            'customizable': [],
            'ExtendedSizing': [],           
            'inStock': [],
            'ComingSoon': [],
            'BestSeller': [],
            'Excluded': [],
            'GiftCard': [],
            'Jersey': [],
            'Launch': [],
            'MemberExclusive': [],
            'NBA': [],
            'NFL': [],
            'Sustainable': [],
            'label': [],
            'prebuildId': [],
            'prod_url':[],

            'color-ID':[],
            'color-Description':[],
            'color-FullPrice':[],
            'color-CurrentPrice':[],
            'color-Discount':[],
            'color-BestSeller':[],
            'color-InStock':[],
            'color-MemberExclusive':[],
            'color-New':[],
            'color-Label':[],
            'color-Image-url':[],
        } 
        
        # Nike shoe categories
        if single_category:
            self.categories=[single_category] 
        else:
            self.categories=[
                'cycling',
                'jordan', 
                'running',
                'golf', 
                'training',
                'tennis',
                'football',
                'basketball',
                'boot',
                'baseball',
                'soccer',
                'hiit',
                'volleyball',
                'lifestyle',
            ]
        
    def __repr__(self):
        return f'{type(self).__name__}({self.__max_number_of_pages!r})'   

    def __log_exception(self,e, verb, url, kwargs):
        '''
        log get exceptions (code from https://stackoverflow.com/questions/16511337/correct-way-to-try-except-using-python-requests-module)
        '''
        print(f'exception - Error {e}, {verb}')
        # raw_tb = traceback.extract_stack()
        # if 'data' in kwargs and len(kwargs['data']) > 500: # anticipate giant data string
        #     kwargs['data'] = f'{kwargs["data"][:500]}...'  
        # msg = f'BaseException raised: {e.__class__.__module__}.{e.__class__.__qualname__}: {e}\n' \
        #     + f'verb {verb}, url {url}, kwargs {kwargs}\n\n' \
        #     + 'Stack trace:\n' + ''.join(traceback.format_list(raw_tb[:-2]))
        # logger.error(msg) 

    def __requests_call(self,verb, url, **kwargs):
        '''
        request wrapper call (code from https://stackoverflow.com/questions/16511337/correct-way-to-try-except-using-python-requests-module)
        '''
        response = None
        exception = None
        try:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.__DEFAULT_REQUESTS_TIMEOUT
            response = requests.request(verb, url, **kwargs)
        except BaseException as e:
            self.__log_exception(e, verb, url, kwargs)
            exception = e
        return (response, exception)

    def __getRating(self,indiv_shoe_soup):
        '''
        try to get the ratings for a given product
        '''
        try:
            return indiv_shoe_soup.find('p', class_='d-sm-ib pl4-sm').text.split()[0]
        except AttributeError:
            return np.NaN

    def __getDescription(self,indiv_shoe_soup): 
        '''
        tries to get the short description of a given product
        '''
        div_desc = indiv_shoe_soup.find('div', attrs={'class':'description-preview'})
        try:
            description = div_desc.find('p').text
        except AttributeError:
            return np.NaN

        return description
            
    def __getDescAndRatings(self, url):
        '''
        gets description and ratings at once, from product url
        '''
        # Gets website page from prod_url
        indiv_shoe_page, exception  = self.__requests_call('get',url)
                
        if not exception :
           indiv_shoe_soup = BeautifulSoup(indiv_shoe_page.text,'html.parser')
           short_desc = self.__getDescription(indiv_shoe_soup)
           rating     = self.__getRating(indiv_shoe_soup) 
        else:
           rating = np.NaN
           short_desc = np.NaN  
                
        return short_desc, rating
    
    def __updateDescriptionAndRatings(self, df, category):
        '''
        iterates over a dataframe to get description and rating for each shoe,from product URL
        '''        
        old_product_id  = None

        for index in tqdm(df[df['category']==category].index, desc=category.upper()):   

            shoe = df.loc[index]
            new_product_id = shoe['productID']

            if new_product_id != old_product_id:
                if self.__DEBUG: print(f">>>New Product {new_product_id}")

                # Gets website page from prod_url
                url = shoe['prod_url']
                
                shor_desc, rating = self.getDescAndRatings(url) 

                if self.__DEBUG: print(f"({shoe['title']}), {short_desc}")
                if self.__DEBUG: print(url)

                old_product_id = new_product_id

            else:
                if self.__DEBUG: print('same product')

            df.at[index,'short_description'] = short_desc
            df.at[index,'rating'] = rating

    def __getProducts(self, category,  anchor=0):
        '''
        retrieve products from website
        '''    
        country = self.__country
        country_language = self.__lan 
        count=self.__page_size

        query = category
        
        # Nike website's API
        url = f'https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=241B0FAA1AC3D3CB734EA4B24C8C910D&country={country}&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace({country})%26filter%3Dlanguage({country_language})%26filter%3DemployeePrice(true)%26searchTerms%3D{query}%26anchor%3D{anchor}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D{count}&language={country_language}&localizedRangeStr=%7BlowestPrice%7D%E2%80%94%7BhighestPrice%7D'
        print(url)

        # Calls API 
        html, exception = self.__requests_call('get',url)
        
        output = json.loads(html.text)

        if self.__DEBUG : print(f'category:{query} anchor:{anchor} count:{count}')

        return output['data']['products']['products']

    def __setFilePrefix(self):
        '''
        set the timestamp to file prefix
        '''
        # get timestamp
        today = (datetime.now()).strftime('%d%b%Y_%H%M')
        timestamp = today.upper()
        
        self.__filePrefix = f'{self.__filePrefix}_{timestamp}'
        
    def __checkPath(self,path):
        '''
        verifies if path exits
        '''
        if not os.path.exists(path):
            os.makedirs(path)
            
    def __writeIntermediateFile(self, category):
        '''
        writes down an intermediate file with last category
        '''  
        
        
        # get number of current file (out of N categories)
        current = self.categories.index(category) + 1
        label = f'{category}_{current}_of_{len(self.categories)}'
        
        file_name = f'{self.__filePrefix}_{label}.csv'

        file_full_path = os.path.join(self.__path,'tmp',file_name) 
        
        # converts data dictionary to dataframe and removes duplicates
        shoes = pd.DataFrame(self.shoeDict)
        shoes = shoes.drop_duplicates(subset='UID')
        
        # get rows only for current category
        shoes = shoes[shoes['category']==category]
        
        shoes.to_csv(file_full_path)
        
        print(f"Intermediate file for category [{category}] saved as '{file_full_path}'")
        if self.__DEBUG: print(f'Saved itermediate file {file_full_path}')
    
    def __writeFinalFile(self, shoes):
        '''
        writes final file name
        '''
        file_name = f'{self.__filePrefix}.csv'
        
        file_full_path = os.path.join(self.__path, file_name)
        
        # Saves dataframe as CSV
        shoes.to_csv(file_full_path)        

    def __writeDictionary(self,category, k, item, color, short_desc, rating, prod_url):
        '''
        add rows to the Data Frame Dictionary
        '''
        # add surrogate IDs for shoe and color    
        self.shoeDict['colorNum'].append(k+1)
        self.shoeDict['UID'].append(item['cloudProductId']+color['cloudProductId'])
        self.shoeDict['productID'].append(item['id'])
        self.shoeDict['cloudProdID'].append(item['cloudProductId'])
        self.shoeDict['shortID'].append(item['id'][-12:]) 
        
        self.shoeDict['type'].append(item['productType'])
        self.shoeDict['category'].append(category)
        self.shoeDict['title'].append(item['title'])
        self.shoeDict['subtitle'].append(item['subtitle'])
        self.shoeDict['short_description'].append(short_desc)
        self.shoeDict['rating'].append(rating)                                                                                 
        
        self.shoeDict['currency'].append(item['price']['currency'])
        self.shoeDict['fullPrice'].append(item['price']['fullPrice'])
        self.shoeDict['sale'].append(item['price']['discounted'])
        self.shoeDict['currentPrice'].append(item['price']['currentPrice'])
        self.shoeDict['TopColor'].append(item['colorDescription'])
        self.shoeDict['channel'].append(item['salesChannel'])
        self.shoeDict['prod_url'].append(prod_url)

        self.shoeDict['customizable'].append(item['customizable'])
        self.shoeDict['ExtendedSizing'].append(item['hasExtendedSizing'])          
        self.shoeDict['inStock'].append(item['inStock'])
        self.shoeDict['ComingSoon'].append(item['isComingSoon'])
        self.shoeDict['BestSeller'].append(item['isBestSeller'])
        self.shoeDict['Excluded'].append(item['isExcluded'])
        self.shoeDict['GiftCard'].append(item['isGiftCard'])
        self.shoeDict['Jersey'].append(item['isJersey'])
        self.shoeDict['Launch'].append(item['isLaunch'])
        self.shoeDict['MemberExclusive'].append(item['isMemberExclusive'])
        self.shoeDict['NBA'].append(item['isNBA'])
        self.shoeDict['NFL'].append(item['isNFL'])
        self.shoeDict['Sustainable'].append(item['isSustainable'])
        self.shoeDict['label'].append(item['label'])
        self.shoeDict['prebuildId'].append(item['prebuildId'])

        # Color Components
        self.shoeDict['color-ID'].append(color['cloudProductId'])
        self.shoeDict['color-Description'].append(color['colorDescription'])
        self.shoeDict['color-FullPrice'].append(color['price']['fullPrice'])
        self.shoeDict['color-CurrentPrice'].append(color['price']['currentPrice'])
        self.shoeDict['color-Discount'].append(color['price']['discounted'])
        self.shoeDict['color-BestSeller'].append(color['isBestSeller'])
        self.shoeDict['color-Image-url'].append(color['images']['portraitURL']) 
        self.shoeDict['color-InStock'].append(color['inStock'])

        self.shoeDict['color-MemberExclusive'].append(color['isMemberExclusive'])
        self.shoeDict['color-New'].append(color['isNew'])
        self.shoeDict['color-Label'].append(color['label'])        
        
    def getData(self):
        '''
        Happy Scraping! 
        Main Method to Scrape Data. It cycles across all elements
        '''
        # reset file prefix for this run
        self.__setFilePrefix()
        # check temp and data directories exist
        self.__checkPath(self.__path)
        self.__checkPath(os.path.join(self.__path,'tmp'))
        
        # count stores the number of rows scrapped per page
        count = self.__count
        anchor = 0
        total_rows = 0

        # get info for each category in the website
        for category in (self.categories): 
            # print(f"Processing category '{category.upper()}'")
            page_number = 0

            # load new pages from the search engine
            for page_number in tqdm(range(self.__max_number_of_pages), desc=category.upper()):

                # Get new html page
                anchor = page_number * self.__page_size  
                output = self.__getProducts(category=category, anchor=anchor)
                page_number +=1
                if self.__DEBUG: print(f'category: {category}, rows: {total_rows}, type(output):{type(output)}')

                # If output is empty, breaks the loop, ending the search for this category
                if output == None:
                    if self.__DEBUG: print(f'End processing searched {i} pages, {rows} rows, {tenis_rows} footwear')
                    break
                else:

                    # Loop through products and print name
                    for j, item in enumerate(output):

                        # pick only footwear, filtering out everything else      
                        if item['productType'] == 'FOOTWEAR': 
                            
                            # Retrieve short description and ratings this makes the process 10X slower
                            prod_url = item['url'].replace('{countryLang}',self.__url_base)
                            
                            short_desc = np.NaN
                            rating = np.NaN
                            if self.__full_description:
                                short_desc, rating = self.__getDescAndRatings(prod_url)

                            # Retrieves features for each color 
                            for k, color in enumerate(item['colorways']):
                                self.__writeDictionary(category, k, item, color, short_desc, rating, prod_url)
                                total_rows +=1
                                
                                if self.__DEBUG :
                                    print(f"{j}:{k}:{item['cloudProductId'][-12]+color['cloudProductId']}:{item['title']},{item['subtitle']},{color['colorDescription']}")
                          
            # writes intermediate file
            self.__writeIntermediateFile(category)      

        
        # Remove Dupes
        shoes = pd.DataFrame(self.shoeDict)
        shoes = shoes.drop_duplicates(subset='UID')
        
        self.__writeFinalFile(shoes)
        
        # final message
        print(f'\nScraping Finished, Total {total_rows} items processed')
        print(f"total rows in dataframe:{len(shoes['UID'])}, unique rows:{len(shoes['UID'].unique())}")
        
        file_full_path = os.path.join(f'{self.__filePrefix}.csv', self.__path) 
        print(f"final dataset file saved as '{file_full_path}'")

        print("removing temporal files")
        shutil.rmtree(f'{self.__path}/tmp')
        
        return shoes

