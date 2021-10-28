# -*- coding: utf-8 -*-
import pandas as pd
from urllib import parse
from bs4 import BeautifulSoup

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
################DAUM###################
########################################
def daum_browser(keyword):
    menus = ["news","cafe","blog", "web"]
    key = parse.quote(keyword)

    for m in menus:
        url = "https://search.daum.net/search?w="+m+"&nil_search=btn&DA=NTB&enc=utf8&q="+key
        g_driver = set_driver(url)
        next_page = True
        while(next_page) :
            WebDriverWait(g_driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME,"list_info")))
            pageString = g_driver.page_source
            next_page = daum_crawler(pageString)

            try:
                element = WebDriverWait(g_driver, 100).until(EC.element_to_be_clickable((By.CLASS_NAME,"btn_next")))
                element.click()
            except:next_page = False

    g_driver.quit()

    result = {"title": title_text, "contents" :contents_text, "url": url_text, "update_time": time_text}   
    df = pd.DataFrame(result)

    return df


def daum_crawler(m_html):
    soup = BeautifulSoup(m_html,'html.parser')
    tab = soup.find_all('ul', class_='list_info')
    start = 0
    if len(tab) > 1: start=1
    for tr in tab[start:] :
        tb=tr.findAll('li')
        for t in tb:
            content = t.find('a', class_='f_link_b')
            title_text.append(content.get_text())
            print(content.get_text())
            url_text.append(content['href'])
            
            content = t.find('span', class_='f_nb')
            if content is not None:
                time_text.append(content.get_text())
            else :
                time_text.append('-')
                
            content = t.find('p', class_='f_eb')
            if content is not None:
                contents_text.append(content.get_text())
            else :
                contents_text.append('-')

    # check wheather there is next page
    btn_next = soup.find('span', class_='btn_next')
    if btn_next is not None :
        if "false" in btn_next['data-paging-active']:
            return False
    return True 

