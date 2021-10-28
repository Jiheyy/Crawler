# -*- coding: utf-8 -*-
import sqlite3
from selenium import webdriver


G_CHROME_DRIVER_PATH = "chromedriver"

def set_driver(url) :
    g_driver = None

    options = webdriver.ChromeOptions()
    # if you do have proxy server to use put in here
    # proxy_list =['0.0.0.0:3128']
    # options.add_argument('--proxy-server=' + proxy_list[random.randint(0, len(proxy_list)-1)])
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36")

    try:
        g_driver = webdriver.Chrome(G_CHROME_DRIVER_PATH, chrome_options=options)
    except:
        print("ONCE AGAIN !!!! LINUX")
        g_driver = webdriver.Chrome('./chromedriver', chrome_options=options)

    # to conceal chromedriver, use these code before access url
    g_driver.get('about:blank')
    g_driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
    g_driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
    g_driver.execute_script("const getParameter = WebGLRenderingContext.getParameter;WebGLRenderingContext.prototype.getParameter = function(parameter) {if (parameter === 37445) {return 'NVIDIA Corporation'} if (parameter === 37446) {return 'NVIDIA GeForce GTX 980 Ti OpenGL Engine';}return getParameter(parameter);};")

    g_driver.get(url)


    return g_driver


def filtering(keyword, df) :
    del_list = []
    print(len(df))
    #df = df.reset_index()
    for idx, d in df.iterrows():
        if (keyword not in d['title']) and (keyword not in d['contents']): 
            del_list.append(idx) 
            
    df.drop(df.index[del_list], inplace = True)
    return df


def db_file(keyword,df) :

    con = sqlite3.connect(keyword+".db")
    curr = con.cursor()
    curr.execute("CREATE TABLE IF NOT EXISTS data(title text, contents text, url text, update_time text)")

    for index, d in df.iterrows():
        sql = "INSERT INTO data(title, contents, url, update_time) VALUES (?,?,?,?)"
        curr.execute(sql, (d.title, d.contents, d.url, d.update_time))
        con.commit()
    con.close()