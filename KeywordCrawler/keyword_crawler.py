# -*- coding: utf-8 -*-
import sys 
import sqlite3
import pandas as pd

from utils import *
from daum import *
from naver import *
from googles import *


# =====================================================
AGENT_NAME = "Keyword_crawler"
G_COMMON_LIB_VER = '0.0.3'
G_COMMON_LIB_DATE = '2021-10-26'
# by min(jh)
# =====================================================

def main(keyword) :
    try:
        daum_result = daum_browser(keyword)
        naver_result = naver_browser(keyword)
        google_result = google_browser(keyword)
    except Exception as e:
        print('error occured :'+e)
     
    df = pd.concat(daum_result, naver_result)
    df = pd.concat(df, google_result)

    df = filtering(keyword, df)
    db_file(keyword, df)
    print(df)


if __name__ == "__main__":
    print("Hello Crawler")
    if (len(sys.argv) is 2) :
        keyword = sys.argv[1]
        try :
            main(keyword)
        except Exception as e:
            print('error occured: '+e)
    else :
        print("How to run : python3 crawler.py Hamster")
