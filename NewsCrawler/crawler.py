# -*- coding: utf-8 -*-
import re
import time
import urllib
import pandas as pd
import sys, os
import sqlite3
import random
from urllib import parse
from bs4 import BeautifulSoup
from datetime import datetime
from slacker import Slacker

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

#cur_d = os.path.dirname(__file__)

# =====================================================
AGENT_NAME = "NEWS_CRAWLER"
G_COMMON_LIB_VER = '0.0.6'
G_COMMON_LIB_DATE = '2020-12-21'
# by min(jh)
# =====================================================
# if its true, it will crawl all data without date filter
FIRST = False
SLACK_TOKEN = 'xoxb-0000000000000000000000000'
SLACK_CHANNEL = '#my_test'

# set keyword what you want to search
KEYWORD_LIST = ["hamster"]
# put keyword what you dont want to crawl
WHITE_LIST = ['mouse']
# if you have sites what you dont want to crawl from, put sites url here
WEBSITE_LIST = ["https://www.jhmin.com"]
# =====================================================

sys.stdout.flush()

G_CHROME_DRIVER_PATH = "./chromedriver"
g_driver = None

title_text=[]
url_text=[]
contents_text=[]
time_text=[]
category_text=[]
result = {}


def set_driver(url) :
    global g_driver

    if g_driver: 
        g_driver.quit()
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # options.add_argument('--disable-extensions')
    # options.add_argument('--headless') # headless option
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    # if you do have proxy server to use put in here
    # proxy_list =['0.0.0.0:3128']
    # options.add_argument('--proxy-server=' + proxy_list[random.randint(0, len(proxy_list)-1)])

    try:
        g_driver = webdriver.Chrome(G_CHROME_DRIVER_PATH, chrome_options=options)
    except Exception as ex:
        print(ex)
        print("ONCE AGAIN !!!! LINUX", flush=True)
        g_driver = webdriver.Chrome(G_CHROME_DRIVER_PATH, chrome_options=options)

    # to conceal chromedriver, use these code before access url
    g_driver.get('about:blank')
    g_driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
    g_driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
    g_driver.execute_script("const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")

    g_driver.get(url)


########################################
################GOOGLE##################
########################################
def google_browser(keyword) :
    global g_driver

    print('Google browsing...', flush=True)

    key = urllib.parse.quote(keyword)
    url = 'https://google.com/search?q='+key+'&lr=lang_ko&tbs=lr:lang_1ko,qdr:d'
    set_driver(url)

    loop = True
    while(loop) : 
        time.sleep(random.randrange(5))
        element = WebDriverWait(g_driver,100).until(EC.presence_of_element_located((By.ID,"rcnt")))
        pageString = g_driver.page_source
        google_crawler(pageString, keyword)
        try:
            element = WebDriverWait(g_driver,10).until(EC.presence_of_element_located((By.ID,"pnnext")))
            element.click()
        except:
            loop = False

    g_driver.quit()


def google_crawler(m_html, keyword):
    global result
    soup = BeautifulSoup(m_html,'html.parser')
    
    table = soup.find_all('div', class_="g")

    for t in table[1:] :
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
            category_text.append('Google')


########################################
################NAVER###################
########################################
def naver_browser(keyword) :
    print('Naver browsing...', flush=True)
    menus = ["news", "view"]

    key = urllib.parse.quote(keyword)

    for m in menus:
        url = "https://search.naver.com/search.naver?f=&query="+key+"&sm=tab_jum&where="+m
        if m == "news":
            if FIRST == False :
                url = url+ "&pd=1"
            try:
                naver_news_browser(url)
            except Exception as ex:
                print('Naver news format error')
                    
        elif m == "view" :
            if FIRST == False : 
                url = url + "&nso=so%3Ar%2Cp%3A1w%2Ca%3Aall"
            try:
                naver_views_browser(url) 
            except Exception as ex:
                print('naver view format error')


def naver_news_browser(url) :
    set_driver(url)
    
    next_page = True
    while(next_page) :
        WebDriverWait(g_driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME,"main_pack")))
        pageString = g_driver.page_source
        naver_news_crawler(pageString)
        try:
            element = WebDriverWait(g_driver, 5).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main_pack"]/div[2]/div/a[2]')))
                
            if element.get_attribute('aria-disabled') == 'true' :
                raise Exception('last page')
            element.click()
        except Exception as ex :next_page = False
    
    g_driver.quit()


def naver_views_browser(url) :
    set_driver(url)

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
                if title != None :
                    print(title.get_text())
                    title_text.append(title.get_text())
                    url_text.append(title['href'])
                    category_text.append('news')
                    break
                
            for t in sh_text: 
                text = c.find('a', class_= t)
                if text != None:
                    contents_text.append(text.get_text())

            try:
                time = c.find_all('span', class_="info")
                try:
                    time = str(time[1]) 
                except:
                    time = str(time[0])
                time = time.split('<span class="info">')
                if len(time) >= 2:
                    time = time[1].split('</span>')
                    time_text.append(time[0])
            except Exception as ex:
                print(ex)
                time_text.append(time)


# 2020.11.17 naver changed its format. 
# cafe -> views
def naver_views_crawler(m_html) :

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
                    if title != None :
                        print(title.get_text())
                        title_text.append(title.get_text())
                        url_text.append(title['href'])
                        new_last_url = title['href']
                        category_text.append('view')
                        break
            except:
                continue

            for t in sh_text: 
                try:
                    text = c.find('div', class_= t)
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


def filtering(df) :
    df = df.reset_index()
    
    del_list = []
   
    for idx, d in df.iterrows():
        key_exist = False
        # if there is no keyword what you want to search. delete 
        for keyword in KEYWORD_LIST:
            if (keyword in d['title']) or (keyword in d['contents']):
                key_exist = True
        # if it containes whitelist keyowrd. delte
        for keyword in WHITE_LIST:
            if (keyword in d['title']) or (keyword in d['contents']):
                key_exist = False
                continue

        if key_exist == False:
            del_list.append(idx)
            continue
	
        # remove if its from website what you dont want
        for w in WEBSITE_LIST:
            if (w in d['url']) :
                del_list.append(idx)
                break
          
        # if its already crawlered before
        if exist_db(d['url']) == True:
            del_list.append(idx)
            continue
    
    df.drop(df.index[del_list], inplace = True)
    return df


def exist_db(url) :
    con = sqlite3.connect("data.db")
    curr = con.cursor()
    curr.execute("CREATE TABLE IF NOT EXISTS data(site text, category text ,title text, contents text, url text, update_time text)")
    df = pd.read_sql_query("SELECT url FROM data WHERE url = '"+url+"'", con)
    con.close()
    
    if len(df) >= 1:
       return True

    return False


def sorting(df) :
    df_google = df.loc[df['category'] == 'Google']
    df_naver = df.loc[df['category'] != 'Google']
    
    
    if len(df_google) > 0 :
        # order by update_time
        df_google = df_google.sort_values(by=['update_time'], ascending=[True])
        df_google = df_google.reset_index()
    
    if len(df_naver) > 0 :
        n_news = df_naver.loc[df_naver['category'] == 'news']
        n_view = df_naver.loc[df_naver['category'] == 'view']
        n_etc = df_naver.loc[df_naver['category'] == 'webkr']

        n_news = n_news.reset_index()
        n_view = n_view.reset_index()

    # if there is no data
    if len(df) == 0:
        return 0

    else:
        now = datetime.now()
        dt_string = now.strftime("%Y.%m.%d %H:%M:%S")
        data = "\n["+dt_string+"] There is new news : "+str(len(df))+"\n1. Naver (total : "+str(len(df_naver))+")"
        slack_massage(data)

    site=[]
    if len(df_naver) > 0 :
        site.append("NAVER")
        data = "* News : "+str(len(n_news))+"\n* View :"+str(len(n_view))+"\n* Etc : "+str(len(n_etc))+"\n"
        slack_massage(data)

    if len(df_google) > 0 :
        site.append("GOOGLE")
        data = "2. Google (total :"+str(len(df_google))+")"
        slack_massage(data)

    if len(df_google)> 0: 
        data_to_send("GOOGLE",df_google)
            
    if len(df_naver) > 0: 
        data_to_send("News", n_news)
        data_to_send("View", n_view)
        data_to_send("Etc", n_etc)
    
    
# formating for Slack
def data_to_send(category, data) :
    if category != "GOOGLE" : site = "NAVER"
    else: site = category
   
    con = sqlite3.connect("data.db")
    curr = con.cursor()
    
    # save data
    if len(data)> 0 :
        d = "=====================["+site+"]["+category+": "+str(len(data))+"]=======================\n"
        slack_massage(d)

        for index,row in data.iterrows():
            if index % 50 == 0 :
                time.sleep(3)
            d = "```["+row.category+" "+str(index+1)+"/"+str(len(data))+"]["+row.update_time+"]["+row.title+"]\n["+row.url+"]\n\n"+row.contents+"```"
            slack_massage(d)
            sql = "INSERT INTO data(title, contents, url, update_time, category) VALUES (?,?,?,?,?)"
            curr.execute(sql, (row.title, row.contents, row.url, row.update_time, row.category))
            con.commit()

    con.close()
    

def slack_massage(msg, channel=SLACK_CHANNEL):
    try :
        sc = Slacker(SLACK_TOKEN)
        sc.chat.post_message(channel, msg)
    except Exception as ex : 
        print('error : ' + ex)


def main() :

    for keyword in KEYWORD_LIST:
        google_browser(keyword)
        naver_browser(keyword)
    
    result = {"title": title_text, "contents" :contents_text, "url": url_text, "update_time": time_text, "category": category_text}   

    try:
    	df = pd.DataFrame(result)
    except Exception as ex:
        print(ex)


    df = df.drop_duplicates("url", keep="first")
    df = filtering(df)

    try:
        sorting(df)
    except Exception as ex:
        print(ex)



if __name__ == "__main__":

    main()

    while(False) :
        print(datetime.now(), flush=True)
        try:  
            main()
        except :
            if g_driver : g_driver.quit()
        time.sleep(60*60)
    
