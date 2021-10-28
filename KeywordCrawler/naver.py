# -*- coding: utf-8 -*-
import time
import pandas as pd
from urllib import parse
from bs4 import BeautifulSoup

from utils import set_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



title_text=[]
url_text=[]
contents_text=[]
time_text=[]
result = {}

########################################
################NAVER###################
########################################
def naver_browser(keyword) :
    menus = ["news", "view"]
    key = parse.quote(keyword)

    print('Naver browsing...')

    for m in menus:
        url = "https://search.naver.com/search.naver?f=&query="+key+"&sm=tab_jum&where="+m
        if m == "news":
            naver_news_browser(url)
        elif m == "view":
            naver_views_browser(url)

    result = {"title": title_text, "contents" :contents_text, "url": url_text, "update_time": time_text}   
    df = pd.DataFrame(result)

    return df
        

def naver_news_browser(url) :
    g_driver = set_driver(url)
    
    next_page = True
    while(next_page) :
        WebDriverWait(g_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,"main_pack")))
        pageString = g_driver.page_source
        naver_news_crawler(pageString)
        try:
            element = WebDriverWait(g_driver, 5).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main_pack"]/div[2]/div/a[2]')))
                
            if element.get_attribute('aria-disabled') == 'true' :
                raise Exception('last page')
            element.click()
            next_page = False
        except Exception as ex :next_page = False
    g_driver.quit()


def naver_views_browser(url) :
    g_driver = set_driver(url)

    next_page = True
    while(next_page) :
        g_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        pageString = g_driver.page_source

        next_page = naver_views_crawler(pageString)
    
    g_driver.quit()    


def naver_news_crawler(m_html) :
    sh_title = ['news_tit']
    sh_text = ['api_txt_lines']

    soup = BeautifulSoup(m_html,'html.parser')
    results = soup.find_all('ul',class_='list_news')
    for result in results:
        content = result.find_all('li')
        for c in content:
            for t in sh_title :
                title = c.find('a', class_= t)
                if title is not None :
                    title_text.append(title.get_text())
                    url_text.append(title['href'])
                    break
                
            for t in sh_text: 
                text = c.find('a', class_= t)
                if text is not None:
                    contents_text.append(text.get_text())

            time = str(c.find('span', class_="info")) 
            time = time.split('<span class="info">')
            if len(time) >= 2:
                time = time[1].split('</span>')
                time_text.append(time[0])


def naver_views_crawler(m_html):
    sh_title = ['total_tit']
    sh_text = ['api_txt_lines']

    if len(url_text) > 1:
        ex_last_url = url_text[len(url_text)-1]
    else : ex_last_url = ''
    new_last_url = ''

    soup = BeautifulSoup(m_html,'html.parser')
    results = soup.find_all('ul',class_='lst_total')

    # if there is no data return
    if len(results) < 1: return False
    
    for result in results:
        content = result.find_all('li')
        for c in content:
            try:
                for t in sh_title :
                    title = c.find('a', class_= t)
                    if title is not None :
                        title_text.append(title.get_text())
                        url_text.append(title['href'])
                        new_last_url = title['href']
                        break
            except:
                continue

            for t in sh_text: 
                try:
                    text = c.find('div', class_= t)
                    if text is not None:
                        contents_text.append(text.get_text())
                except:
                    contents_text.append('-')
            try:
                time = str(c.find('span', class_="sub_time")) 
                time = time.split('<span class="sub_time sub_txt">')
                if len(time) >= 2:
                    time = time[1].split('</span>')
                    time_text.append(time[0])
            except: 
                time_text.append('-')

    if ex_last_url == new_last_url :return False

    return True