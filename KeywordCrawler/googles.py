# -*- coding: utf-8 -*-
from urllib import parse
from bs4 import BeautifulSoup
import pandas as pd

from utils import set_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


title_text=[]
url_text=[]
contents_text=[]
time_text=[]
result = {}

########################################
################GOOGLE##################
########################################
def google_browser(keyword) :
    print('Google browsing...')

    key = parse.quote(keyword)
    url = "https://google.com/search?q="+key
    #set_driver.get(
    g_driver = set_driver(url)
    #페이지 끝까지 서칭
    loop = True
    while(loop) : 
        element = WebDriverWait(g_driver, 60).until(EC.presence_of_element_located((By.ID,"rso")))
        pageString = g_driver.page_source
        google_crawler(pageString, keyword)
        try:
            element = WebDriverWait(g_driver,60).until(EC.presence_of_element_located((By.ID,"pnnext")))
            element.click()
        except:
            loop = False

    g_driver.quit()


    result = {"title": title_text, "contents" :contents_text, "url": url_text, "update_time": time_text}   
    df = pd.DataFrame(result)

    return df


def google_crawler(m_html, keyword) :
    global result
    soup = BeautifulSoup(m_html,'html.parser')

    table = soup.find_all('div', class_="g")
    for t in table[1:]:
        try:
            title = t.find('h3').get_text()
            url = t.find('a')['href']
        except:
            continue

        try:
            contents = t.find('div', class_="VwiC3b yXK7lf MUxGbd yDYNvb lyLwlc lEBKkf")
            contents= contents.get_text()
        except: 
            contents = '-'

        try:
            time = t.find('span', class_="MUxGbd wuQ4Ob WZ8Tjf") 
            time = time.get_text().replace('—', '')
        except: 
            time = '-'    
    
        if (keyword in title) or (keyword in contents):
            title_text.append(title)
            url_text.append(url)
            contents_text.append(contents)
            time_text.append(time)



def filtering(keyword, df) :
    del_list = []
    df = df.reset_index()
    for idx, d in df.iterrows():
        if (keyword not in d['title']) and (keyword not in d['contents']): 
            del_list.append(idx) 
            
    df.drop(df.index[del_list], inplace = True)
    return df
