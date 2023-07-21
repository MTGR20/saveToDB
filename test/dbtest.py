#!/usr/bin/env python
# coding: utf-8

# In[13]:


#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
#from selenium.webdriver import ActionChains
#이미지 다운로드
from urllib.request import urlretrieve
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time
from datetime import datetime
import MySQLdb

import speech_recognition as sr
from gtts import gTTS
import os
import playsound

import urllib
import ssl
import shutil

import numpy as np
import platform
from PIL import ImageFont, ImageDraw, Image
from matplotlib import pyplot as plt

import uuid
import json
import cv2
import requests
import re

import sys


HomeUrl = "https://front.homeplus.co.kr/"
GooUrl = "https://www.google.co.kr/"
api_url = "api_url" #수정하기 Naver Clovar
secret_key = "secret_key" #수정하기 Naver Clovar
dir_path = "dir_path" #수정하기 이미지 저장할 경로
path_folder = "path" #수정하기 (=dir_path)
filename ='C:/Users/User/test/voice.mp3'#수정하기 (보이스 파일 저장할 경로)


def speak(text):
    tts = gTTS(text=text, lang='ko')
    tts.save(filename) # 파일을 만들고,
    playsound.playsound(filename) # 해당 음성파일을 실행(즉, 음성을 말함)
    os.remove(filename) # <---- 이부분이 없으면 퍼미션 에러 발생(아마도 파일을 연 상태에서 추가적인 파일생성 부분에서 에러가 발생하는 것으로 보임)

# 사용자 음성 검색
def start():
    
    
#     # 안내 방송(음성)
#     speak("안녕하세요. 검색하실 상품을 말씀해주세요.")
    
#     # 사용자 음성 듣기
#     r = sr.Recognizer()
#     mic = sr.Microphone(device_index = 1)
    
#     with mic as source:
#         audio = r.listen(source, timeout = 3)

#     query_txt = r.recognize_google(audio, language="ko-KR")
#     print(query_txt)

###############################################################################################################################
# DB에 상품 정보 저장
# DB start, close : 실행 코드 맨 첫 부분, 끝 부분(사용자가 창 닫을 때)에 추가하기
# save_products_to_db: get_product(key) 함수 내부에서 사용
# Tips!!: tab 들여쓰기 단축키, shift+tab 내어쓰기 단축키

    # 크롬드라이버 실행
    driver = webdriver.Chrome()
    #크롬 드라이버에 url 주소 넣고 실행
    driver.get(HomeUrl)

    conn = MySQLdb.connect(
        user="crawl_usr",
        passwd="test1",
        host="localhost",
        db="homeplus"
    )
    # 페이지가 완전히 로딩되도록 3초동안 기다림
    time.sleep(3)
    
    query_txt = "라면"
    driver.find_element(By.NAME, "keyword").send_keys(query_txt, Keys.ENTER)
    time.sleep(5) # sleep 안걸어주면 한줄당 3개의 상품들만 출력됨
    
    # 커서 생성하기
    cursor = conn.cursor()
    
    # 실행할 때마다 다른 값이 나오지 않도록 테이블을 제거해두기
    cursor.execute("DROP TABLE IF EXISTS page_items")
    
    #cursor.execute('CREATE TABLE IF NOT EXISTS page_items(ranks INT, name TEXT, price TEXT, link CHAR(255))')
    cursor.execute('CREATE TABLE page_items(ranks INT, name TEXT, price TEXT, link CHAR(255))')

    prods = driver.find_elements(By.CLASS_NAME, 'unitItemBox')

    ranks = 1
    for prod in prods :
        name = prod.find_element(By.CLASS_NAME, "css-12cdo53-defaultStyle-Typography-ellips").text
        price = prod.find_element(By.CLASS_NAME, "priceValue").text
        link = prod.find_element(By.CLASS_NAME, "productTitle").get_attribute('href')
#         print(name)
#         print(price)
#         print(link)    
        cursor.execute("INSERT INTO page_items VALUES (%d, '%s', '%s', '%s')"%(ranks, name, price, link))
        ranks += 1
        
        cursor.execute("SELECT link FROM page_items WHERE ranks < 41")
    db_link = cursor.fetchall()
    print("현재 테이블의 데이터 수 : {}".format(len(db_link)))
    print(db_link[0])
    print(type(db_link[0]))
    
    ranks = 0
    cursor.execute('ALTER TABLE page_items ADD src_link CHAR(255)')
    for link in db_link:
        ranks += 1
        driver.get(''.join(link))
#         print(":: " + ''.join(link))
        time.sleep(3)
        try:
            # 영양정보 이미지 위치로 이동
            driver.execute_script("window.scrollTo(0, 3000)")
            element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME,"prodLabelImg"))
            )
        except:
            print("error")

        base = driver.find_element(By.CLASS_NAME,"prodDetailArea").find_elements(By.TAG_NAME,'img')

        src_link = base[-1].get_attribute('src')
        cursor.execute("UPDATE page_items SET src_link='%s' WHERE ranks='%d'" % (src_link, ranks))
        print(src_link)
    
        
    # 커밋
    conn.commit()
    # 연결 종료
    conn.close


start()


# In[ ]:





# In[ ]:




