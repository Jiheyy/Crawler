# -*- coding: utf-8 -*-
from urllib import parse
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import urllib
import pandas as pd
import sys
import sqlite3
from random import randint
import pyperclip
#import os
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from wordpress_xmlrpc import Client, WordPressPost, WordPressPage
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.methods.users import GetUserInfo


# =============================================================================
AGENT_NAME = "KinCrawler"
G_COMMON_LIB_VER = '0.0.2'
G_COMMON_LIB_DATE = '2021-10-19'


first = False # if first = True : it will crawl without time limit
NAVER_ID = 'put your naver id'
NAVER_PW = 'put your naver pw'
WORDPRESS_URL = 'put your wordpress link. it would be simillar with "http://0.0.0.0/wordpress' 
WORDPRESS_ID = 'put your wordpress id'
WORDPRESS_PW = 'put your wordpress pw'
# =============================================================================


G_CHROME_DRIVER_PATH = "chromedriver"
g_driver = None
client = Client(WORDPRESS_URL+'/xmlrpc.php', WORDPRESS_ID, WORDPRESS_PW)

title_text=[]
url_text=[]
contents_text=[]
time_text=[]
result = {}


def set_driver(url) :
    global g_driver

    if g_driver: 
        g_driver.quit()

    options = webdriver.ChromeOptions()
    # if you have proxy then remove '#' and write down your proxy IP:port
    #proxy_list = ['0.0.0.0:2198']
    #options.add_argument('--proxy-server=' + proxy_list[randint(0, len(proxy_list)-1)])
    
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    try:
        g_driver = webdriver.Chrome(G_CHROME_DRIVER_PATH, chrome_options=options)
    except:
        print("ONCE AGAIN !!!! LINUX")
        g_driver = webdriver.Chrome(G_CHROME_DRIVER_PATH, chrome_options=options)
    
    # to hide chromedriver 
    g_driver.get('about:blank')
    g_driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
    g_driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
    g_driver.execute_script("const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")

    g_driver.get(url)
    time.sleep(5)


########################################
################NAVER###################
########################################

def naver_browser(keyword) : 
    key = urllib.parse.quote(keyword)

    print('Naver browsing for '+keyword+'...')

    url = 'https://search.naver.com/search.naver?where=kin&kin_display=10&qt=&title=0&&answer=0&grade=0&choice=0&sec=0&query='+key+'&c_id=&c_name=&nso=so%3Ar%2Ca%3Aall%2Cp%3A1d&kin_age=0'
    set_driver(url)

    next_page = True
    while(next_page) :
        WebDriverWait(g_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,"main_pack")))
        pageString = g_driver.page_source
        time.sleep(1)
        naver_crawler(pageString)
        try:
            element = WebDriverWait(g_driver, 5).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main_pack"]/div[2]/div/a[2]')))
            if element.get_attribute('aria-disabled') == 'true':
                raise Exception('last page')
            element.click()
        except Exception as ex:
            next_page = False

    g_driver.quit()


def naver_crawler(m_html) :
    soup = BeautifulSoup(m_html,'html.parser')
    results = soup.find_all('li',class_='bx _svp_item')
    for result in results:
        title = result.find('div', {'class': 'kin_wrap'}).find('div', {'class':'question_area'}).find('div', {'class': 'question_group'}).find_all('a')
        title_text.append(title[0].get_text())
        url = title[0]['href'].split('&qb')
        url_text.append(url[0])

        contents = result.find('div', {'class':'kin_wrap'}).find('div', {'class':'answer_area'}).find('div', {'class':'answer_group'})
        answer = contents.find_all('a')
        contents_text.append(answer[0].get_text())

        post_time = contents.find('div',{'class': 'elss'}).find_all('span')
        time_text.append(post_time[0].get_text())

        

def filtering(filter_keywords , df) :
    del_list = []
    for idx, d in df.iterrows():
        con = sqlite3.connect("data.db")
        curr = con.cursor()
        curr.execute("CREATE TABLE IF NOT EXISTS data(title text, contents text, url text, update_time text)")
        exist_df = pd.read_sql_query("SELECT url FROM data WHERE url = '"+d['url']+"'", con)

        if len(exist_df) >= 1:
            del_list.append(idx)
            continue

        title = str(d['title'])
        contents = str(d['contents'])
        for key in filter_keywords:
            if key in title or key in contents :
                print(d['url']+' is filtered by '+key)
                del_list.append(idx)
                continue

    df.drop(df.index[del_list], inplace = True)

    if len(df) >= 1:
        for index, d in df.iterrows() :
            sql = "INSERT INTO data(title, contents, url, update_time) VALUES (?,?,?,?)"
            curr.execute(sql, (d.title, d.contents, d.url, d.update_time))
            con.commit()
        con.close()

    # print("NEW DATA")
    # print(df)

    return df


def get_filter(post_name) :
    lists = []
    posters = client.call(posts.GetPosts({'post_type':'page'}, result_class=WordPressPage))
    for post in posters:
        if str(post) == post_name:
            contents = post.content
            keywords = contents.split('<!-- wp:paragraph -->\n<p>')
            for k in keywords[1:]:
                lists.append(k.replace('</p>\n<!-- /wp:paragraph -->', '').replace('\n\n', ''))
            return lists



def get_keyword(post_name) :
    lists = []
    posters = client.call(posts.GetPosts({'post_type':'page'}, result_class=WordPressPage))
    for post in posters:
        if str(post) == post_name:
            contents = post.content
            keywords = contents.split('<tr><td>')
            for k in keywords[1:]:
                lst = k.replace('<!-- wp:table -->', '').replace('<!-- /wp:table -->', '').replace('\n', '').replace('<figure class="wp-block-table"><table><tbody>','').replace('<br>','').replace('</td>','').replace('</tr>','').replace('</tbody></table></figure>', '')
                if lst != '<td>':
                    lst = lst.split('<td>')
                    lists.append(lst)
            
            return lists

def selflogin() :
    # wordpress login
    time.sleep(5)
    g_driver.find_element_by_id('user_login').send_keys(WORDPRESS_ID)
    g_driver.find_element_by_id('user_pass').send_keys(WORDPRESS_PW)
    g_driver.find_element_by_id('wp-submit').click()
    time.sleep(2)

    # naver login
    g_driver.execute_script('window.open("about:blank", "_blank");')
    time.sleep(2)
    tabs = g_driver.window_handles
    g_driver.switch_to_window(tabs[1])
    g_driver.get('https://nid.naver.com/nidlogin.logout')
    time.sleep(3)

    # self_login
    n_id = g_driver.find_element_by_id('id')
    g_driver.execute_script("arguments[0].value='"+NAVER_ID+"'", n_id)
    time.sleep(1)
    n_pw = g_driver.find_element_by_id('pw')
    g_driver.execute_script("arguments[0].value='"+NAVER_PW+"'", n_pw)
    time.sleep(1)
    g_driver.find_element_by_id('log.login').click()
    time.sleep(2)


def write(title, contents, success_post) :
    g_driver.execute_script('window.open("about:blank", "_blank");')
    tabs = g_driver.window_handles
    g_driver.switch_to_window(tabs[2])

    # change
    url = WORDPRESS_URL+'/wp-admin/admin.php?page=kboard_admin_view_1&kboard_id=1&view_iframe=1&iframe_id=5fc66accbcac5&mod=editor&pageid=1'
    g_driver.get(url)

    time.sleep(2)
    g_driver.find_element_by_id('title').send_keys(title)
    g_driver.find_element_by_id('kboard_content').send_keys(contents)
    
    # category : success
    if success_post :g_driver.find_element_by_xpath('//*[@id="kboard-tree-category-1"]/option[2]').click()
    # category : failed
    else : g_driver.find_element_by_xpath('//*[@id="kboard-tree-category-1"]/option[3]').click()
    time.sleep(2)
    g_driver.find_element_by_xpath('//*[@id="kboard-default-editor"]/form/div[10]/div[2]/button').click()
    time.sleep(2)
    g_driver.close()
    g_driver.switch_to.window(tabs[1])
    time.sleep(2)

# write comment
def comment1(url, comment) :
    g_driver.execute_script('window.open("about:blank", "_blank");')
    tabs = g_driver.window_handles
    g_driver.switch_to_window(tabs[len(tabs)-1])
    g_driver.get(url)
    time.sleep(2)

    #popup remover
    try:
        g_driver.find_element_by_xpath('//*[@id="rouletteEndAlertLayer"]/div[1]/div/div/div[3]/button[1]').click()
    except :pass

    time.sleep(2)
    g_driver.find_element_by_id("answerWriteButton").click()
    pyperclip.copy(comment)
    print('copy')
    time.sleep(3)
    #g_driver.find_element_by_xpath('//*[@id="smartEditor"]/div/div/div/header/div[2]/ul/li[3]').click()
    # windows, ubuntu -> paste key: ctrl + v
    ActionChains(g_driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
    # mac -> paste key: cmd + v
    #ActionChains(g_driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
    
    time.sleep(5)
    g_driver.find_element_by_id('answerRegisterButton').click()
    time.sleep(5)
    g_driver.close()
    g_driver.switch_to_window(tabs[0])
        
        

# write comment 2
def comment2(url, comment) :
    tabs = g_driver.window_handles
    g_driver.switch_to_window(tabs[len(tabs)-1])

    g_driver.find_element_by_xpath('//*[@id="cmtstr_0"]').click()
    time.sleep(2)
    pyperclip.copy(comment)

    g_driver.find_element_by_xpath('//*[@id="questionCommentListArea"]/div[1]/fieldset/div[1]/textarea').click()
    # windows, ubuntu -> paste key: ctrl + v
    ActionChains(g_driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
    #ActionChains(g_driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
    g_driver.find_element_by_xpath('//*[@id="questionCommentListArea"]/div[1]/fieldset/div[2]/button').click()
    time.sleep(3)

    g_driver.close()
    g_driver.switch_to.window(tabs[0])


def comment_generator(keyword, title):
    t_keyword = keyword[0]
    comment = keyword[1]

    title = title.split(' ')
    t_title = ''
    
    random_num1 = randint(1, len(title)-1)
    random_num2 = randint(0, random_num1-1)

    for i in range(random_num2, random_num1):
        t_title += title[i]
    
    comment += '\n\n'+ t_title.replace(t_keyword, '')
    return comment


def main() :

    global first, title_text, contents_text, url_text, time_text, filter_keywords
    first= False
    comment_num = 0
    post_num = 0

    keywords = get_keyword('KEYWORD')
    filter_keywords = get_filter('FILTER')

    for keyword in keywords:

        title_text=[]
        contents_text=[]
        url_text=[]
        time_text=[]
        
        naver_browser(keyword[0])
        
        result = {"title": title_text, "contents" :contents_text, "url": url_text, "update_time": time_text}
        df = pd.DataFrame(result)
        df = df.drop_duplicates("url", keep="first")
        df = filtering(filter_keywords, df)

        if g_driver : g_driver.quit()
        if len(df) < 1 : continue
        
        url = WORDPRESS_URL
        set_driver(url)
        selflogin()

        for d in df.itertuples():
            success_post = True
            comment = comment_generator(keyword, d.title)
            try:
                comment_num += 1
                comment1(d.url, comment)
            except Exception as ex:
                print('failed1')
                try :
                    comment2(d.url, comment)
                except Exception as ex:
                    comment_num -=1
                    success_post = False
                    print('failed2')
                    print(ex)
                
            finally: 
                time.sleep(10)

            title = keyword[0]+'|'+d.title
            content = '['+d.update_time+']\n' +d.url+'\n' +d.contents
            try:
                post_num+=1
                write(title, content, success_post)
            except Exception as ex:
                print('posting failed')
                post_num -=1

    print(post_num)
    print(comment_num)
    
    if g_driver: g_driver.quit()


if __name__ == "__main__":

    main()
    while(True) :
        print(datetime.now(), flush=True)
        try:  
            main()
            print('bye~')
            time.sleep(60*60*2)
        except :
            if g_driver : g_driver.quit()
            print('bye!')
            time.sleep(60*60*2)
