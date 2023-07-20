#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
filename ='voiceFile'#수정하기 (보이스 파일 저장할 경로)

# get_key()
# start_db(), close_db()
# get_product(상품명) : 알러지 정보, 상품 정보(이름, 가격, 링크) 리턴 

# 반환 안내 STT txt 만들기
# + 중간에 멈출 수 있도록 하는 변수 필요

#################################################################################################################################
# main
def main(argv):
    opt = int(argv[1])
    
    #opt로 db connect 관리, product 상품 정보 txt로 호출, speak() 실행,  
    
    if (opt<-1): #db connect 시작 (맨처음 1번 호출)
        start_db()
    else if (opt==0):
        close_db()
    else if (opt==1): #db connect 닫기 (맨마지막 1번 호출)
        return (get_product(key))
    else if (opt>1):
        speak(argv[2])

if __name__ == "__main__": #argv[1]: opt , #argv[2]: 상품명
    main(sys.argv)


###############################################################################################################################
# STT: 음성 검색 안내 및 음성 검색어 추출
# 음성 버튼 클릭 시 get_key() 실행

def speak(text):
    tts = gTTS(text=text, lang='ko')
    tts.save(filename) # 파일을 만들고,
    playsound.playsound(filename) # 해당 음성파일을 실행(즉, 음성을 말함)
    os.remove(filename) # <---- 이부분이 없으면 퍼미션 에러 발생(아마도 파일을 연 상태에서 추가적인 파일생성 부분에서 에러가 발생하는 것으로 보임)

# 사용자 음성 검색
def get_key ():
    # 안내 방송(음성)
    speak("안녕하세요. 검색하실 상품을 말씀해주세요.")
    
    # 사용자 음성 듣기
    r = sr.Recognizer()
    mic = sr.Microphone(device_index = 1)
    
    with mic as source:
        audio = r.listen(source, timeout = 3)

    query_txt = r.recognize_google(audio, language="ko-KR")
    #print(query_txt)
    return (query_txt)

###############################################################################################################################
# DB에 상품 정보 저장
# DB start, close : 실행 코드 맨 첫 부분, 끝 부분(사용자가 창 닫을 때)에 추가하기
# save_products_to_db: get_product(key) 함수 내부에서 사용
# Tips!!: tab 들여쓰기 단축키, shift+tab 내어쓰기 단축키

def start_db():
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
    
def close_db():
    # 연결 종료
    conn.close
    
def save_products_to_db(key):
    driver.find_element(By.NAME, "keyword").send_keys(key, Keys.ENTER)
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
        #print(name)
        #print(price)
        #print(link)    
        cursor.execute("INSERT INTO page_items VALUES (%d, '%s', '%s', '%s')"%(ranks, name, price, link))
        ranks += 1
    
    # 커밋
    conn.commit()
    return ranks, name, price, link

###############################################################################################################################
# get_product (검색어): 검색어로 크롤링 후 DB에 상품정보 저장 및 OCR을 통해 알러지 정보를 포함한 상품 정보 리스트 리턴함

# 실행코드 : 알러지 정보 가져올 때 실행
def get_product (key):
    name_list, price_list,link_list = save_products_to_db(key) # 입력받은 검색어로 크롤링해 상품정보를 DB에 저장함
    links=get_img(link_list) # 링크에 접속해 영양 정보 이미지를 가져옴
    is_empty_file(dir_path) # 빈 디렉토리 체크 (빈 디렉토리로 만듦)
    get_preimg(name_list,links) # 접속한 링크에서 받은 이미지를 디렉토리에 듐 
    img_path=get_dirimgs(name_list,dir_path) #
    re=naver_clova(img_path) # 클로바 OCR 실행
    stts_allergy=find_allergy(name_list,re) # 알러지 정보 추출
    return stts_allergy, name_list, price_list, link_list;

def get_img(link_list):
    HomeUrl=link_list[0:10].copy()
    results = []
    for link in HomeUrl:
        re=[]
        driver.get(link)
        time.sleep(10)
        try:
            # 영양정보 이미지 위치로 이동
            driver.execute_script("window.scrollTo(0, 3000)")
            element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME,"prodLabelImg"))
            )
        except:
            print("error")

        base = driver.find_element(By.CLASS_NAME,"prodDetailArea").find_elements(By.TAG_NAME,'img')
        for img in base:
            src_link = img.get_attribute('src')
            re.append(src_link)
        results.append(re)
        print(re)
        
    return results

def is_empty_file(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        raise ValueError("해당 경로를 확인해주세요")
    os.mkdir(path)

def get_preimg(name_list,results):
    ssl._create_default_https_context = ssl._create_unverified_context
    if not os.path.isdir(path_folder):
        os.mkdir(path_folder)
    i = 0
    #상품 광고
    for li in results:
        print(li[-1])
        img_link=li[-1]
        
        urllib.request.urlretrieve(img_link, path_folder + f'{name_list[i]}.jpg')
        i += 1

def img_show(title='image', img=None, figsize=(8 ,5)):
    plt.figure(figsize=figsize)
 
    if type(img) == list:
        if type(title) == list:
            titles = title
        else:
            titles = []
 
            for i in range(len(img)):
                titles.append(title)
 
        for i in range(len(img)):
            if len(img[i].shape) <= 2:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_GRAY2RGB)
            else:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_BGR2RGB)
 
            plt.subplot(1, len(img), i + 1), plt.imshow(rgbImg)
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])
 
        plt.show()
    else:
        if len(img.shape) < 3:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
 
        plt.imshow(rgbImg)
        plt.title(title)
        plt.xticks([]), plt.yticks([])
        plt.show()

def get_dirimgs(name_list,path):
    root_dir = path # 디렉토리
 
    img_path_list = []
    possible_img_extension = ['.jpg', '.jpeg', '.JPG', '.bmp', '.png'] # 이미지 확장자들
 
    for (root, dirs, files) in os.walk(root_dir):
        if len(files) > 0:
            for file_name in files:
                if os.path.splitext(file_name)[1] in possible_img_extension:
                    img_path = root + file_name
                
                    # 경로에서 \를 모두 /로 바꿔줘야함
                    img_path = img_path.replace('\\', '/') # \는 \\로 나타내야함         
                    img_path_list.append(img_path)
    result=[]             
    for name in name_list:
        for p in img_path_list:
            if(p.find(name)!=-1):
                    result.append(p)
                    break
    return result

def naver_clova(paths):
    path = paths
    re=[]
    for p in path:
        print(p)
        
        files = [('file', open(p,'rb'))]
        request_json = {'images': [{'format': 'jpg',
                                    'name': 'demo'
                                   }],
                        'requestId': str(uuid.uuid4()),
                        'version': 'V2',
                        'timestamp': int(round(time.time() * 1000))
                       }
 
        payload = {'message': json.dumps(request_json).encode('UTF-8')}
 
        headers = {
          'X-OCR-SECRET': secret_key,
        }
 
        response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
        result = response.json()
        
        all=[]
        for field in result['images'][0]['fields']:
            text = field['inferText']
            all.append(text)
#        print(all)
        re.append(all)
    return re

def replace_string(all):
    specialchars="{}[](),/:을"
    
    for i in specialchars:
        #print(i)
        for a in range(len(all)):
            if(all[a]==i):
                all=all.replace(i,' ')
    return all

def string_pre(all):
    new_all=[]
    for a in range(len(all)):
        #특수문자 처리
        all[a]=replace_string(all[a])

        #포함제거
        poham=all[a].find("포함")
        if(poham!=-1):
            all[a]=''
        
        split_point=0
        sp_str=all[a].split(" ")
        split_point+=len(sp_str)

        for i in range(len(sp_str)):
            new_all.append(sp_str[i])
        
    new_all = list(filter(None, new_all))
    
    return new_all

def find_fac(all):
    fac_keyword=['사용','제품','같은','시설','제조']
    fac_index=[]
    for a in range(len(all)):
        for f in fac_keyword:
            if(all[a].find(f)!=-1):
                fac_index.append(a)
    fac_index.sort()
    return fac_index
      

def find_facnum(fac_index):
    f=0
    point=0
    for i in range(len(fac_index)-1):
        if(fac_index[i+1]-fac_index[i]<2):
            if(point==0):
                f=fac_index[i]
            point+=1
            if(point>=3):
                return f
        else:
            f=0
            point=0
    return -1
        
def find_index(all,keyword):
    index=[]
    keys=[]
    for a in range(len(all)):
        for k in keyword:
            num = all[a].find(k)    
            if(num!=-1):    
                all[a]=k
                index.append(a)
                break
    index.sort()
    return index

def remove_fac(pre_re,food_index,fac_num):
    if(fac_num==-1):
        new_food_index=[]
        new_food_index.append(food_index)
        return new_food_index
    food_index.append(fac_num)
    food_index.sort()
    f=fac_num
    fac=food_index.index(fac_num)
    for i in reversed(food_index[:fac]):
        if(f-i<=2):
            f=i
        else:
            break

    new_food_index=[]
    new_food_index.append(food_index[:food_index.index(f)])

    if(len(food_index)-1>food_index.index(fac_num)):
        new_food_index.append(food_index[food_index.index(fac_num):])
    return new_food_index
    
def stt_string(name,pre_re,allergy):
    stt=""
    print(f"<{name}>의 알러지유발성분 입니다.")
    set_allergy=[]
    for a in allergy:
        for i in a:
            set_allergy.append(pre_re[i])
    result=set(set_allergy)
    for a in result:
        stt+=a
        stt+=" "
        print(a,end=' ')
    print("입니다.")
    return stt

def find_allergy(name_list,re):
    keyword= ['메밀','밀','대두','복숭아','토마토'\
            ,'우유','치즈','굴','가리비','전복','홍합','땅콩','계란','달걀'\
            ,'고등어','멸치','명태','가자미','명태','장어','대구','참치','연어'\
            ,'랍스터','오징어','게','새우','양고기','소고기','돼지고기','아황산포함식품'\
            ,'번데기','닭고기','쇠고기','오징어','잣','오이','토마토','당근'\
            ,'셀러리','감자','마늘','양파','딸기','키위','망고','바나나','감귤'\
            ,'사과','복숭아','밤','보리','옥수수','쌀','밀가루','참깨','땅콩','콩'\
            ,'헤이즐럿','호두','카카오','아모든','해바라기씨','CCD항원','효모'\
            ,'올리브','아카시아','쑥'
           '난류','알류','견과류','육류','갑각류','조개류','아황산류']
    ite=0
    stts=[]
    for i in re:
        print(f"--------------{name_list[ite]}-----------------")
        pre_re=string_pre(i)
        food_index=find_index(pre_re,keyword)
        fac_index=find_fac(pre_re)
        fac_num=find_facnum(fac_index)
        allergy=remove_fac(pre_re,food_index,fac_num)
        stt=stt_string(name_list[ite],pre_re,allergy)
        stts.append(stt)
        ite+=1
    return stts
