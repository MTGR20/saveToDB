#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver import ActionChains
# 이미지 다운로드
from urllib.request import urlretrieve
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 페이지 로딩을 기다리는데 사용할 time 모듈 import
import time
import pymysql

import urllib
import uuid
import json
import requests

import SttAndTts

HomeUrl = "https://front.homeplus.co.kr/"
GooUrl = "https://www.google.co.kr/"
api_url = "https://y3hw7c8u65.apigw.ntruss.com/custom/v1/23682/24dc560540b3d588ce29f91ed67fc738a362844154f27397656afd093c2d57b3/general"  # 수정하기 Naver Clovar
secret_key = "V2VJTVNQeFpHZ1dObHVTVnduYW9WeG90T1hPd3hJV1Y="  # 수정하기 Naver Clovar

user = "root"
passwd = "root"
host = "localhost"
db = "test_db"

'''
user = "root"
passwd = "lch741062@"
host = "localhost"
db = "test_db"

'''


#################################################################################################################################
# DB에 상품 정보 저장
# Tips!!: tab 들여쓰기 단축키, shift+tab 내어쓰기 단축키

def start(query_txt):
    driver = webdriver.Chrome(executable_path="/Users/leechanho8511/PycharmProjects/ssu_merge/chromedriver")  # 크롬 드라이버 실행
    driver.get(HomeUrl)  # 크롬 드라이버에 url 주소 넣고 실행

    conn = pymysql.connect(
        user=user,
        passwd=passwd,
        host=host,
        db=db
    )
    time.sleep(3)  # 페이지가 완전히 로딩되도록 3초동안 기다림
    driver.find_element(By.NAME, "keyword").send_keys(query_txt, Keys.ENTER)
    time.sleep(5)  # sleep 안 걸어주면 한줄당 3개의 상품만 출력됨

    ############################################################### 크롤링 뷰 invisible하게
    ############################################################### 검색했을 때 아무것도 안 나오는 경우 처리?

    cursor = conn.cursor()  # 커서 생성

    cursor.execute("DROP TABLE IF EXISTS page_items")  # 실행할 때마다 다른 값이 나오지 않도록 테이블을 제거해두기
    # cursor.execute('CREATE TABLE IF NOT EXISTS page_items(ranks INT, name TEXT, price TEXT, link CHAR(255))')
    cursor.execute('CREATE TABLE page_items(ranks INT, name TEXT, price TEXT, link CHAR(255))')

    prods = driver.find_elements(By.CLASS_NAME, 'unitItemBox')

    ranks = 1
    for prod in prods:
        name = prod.find_element(By.CLASS_NAME, "css-12cdo53-defaultStyle-Typography-ellips").text
        price = prod.find_element(By.CLASS_NAME, "priceValue").text
        link = prod.find_element(By.CLASS_NAME, "productTitle").get_attribute('href')

        cursor.execute("INSERT INTO page_items VALUES (%d, '%s', '%s', '%s')" % (ranks, name, price, link))
        ranks += 1
        cursor.execute("SELECT link FROM page_items WHERE ranks < 11")

    db_link = cursor.fetchall()
    print("현재 테이블의 데이터 수 : {}".format(len(db_link)))

    ranks = 0
    cursor.execute('ALTER TABLE page_items ADD (main_picture CHAR(255), src_link CHAR(255), Allergy_extraction TEXT)')
    for link in db_link:
        ranks += 1
        driver.get(''.join(link))
        time.sleep(3)
        main_link = driver.find_element(By.CLASS_NAME, "thumbSliderWrap").get_attribute('src')

        ### 대표 이미지 저장 ###
        try:
            element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "thumbSlideItem"))
            )
        except:
            print("error")

        main_link = driver.find_element(By.CLASS_NAME, "prodTopImgWrap").find_elements(By.TAG_NAME, 'img')
        main_picture = main_link[0].get_attribute('src')

        ### 영양 정보 이미지 db 저장 ###
        try:
            # 영양정보 이미지 위치로 이동
            driver.execute_script("window.scrollTo(0, 3000)")
            element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "prodLabelImg"))
            )
        except:
            print("error")

        base = driver.find_element(By.CLASS_NAME, "prodDetailArea").find_elements(By.TAG_NAME, 'img')
        src_link = base[-1].get_attribute('src')

        # 상품 메인 이미지, 영양 정보 이미지 src -> db에 저장
        cursor.execute(
            "UPDATE page_items SET main_picture='%s', src_link='%s' WHERE ranks='%d'" % (main_picture, src_link, ranks))
        # print(src_link)
        print(src_link)

        re = naver_clova(src_link)  # 클로바 OCR 실행
        stts_allergy = find_allergy(re)  # 알러지 정보 추출
        string_allergy = ' '.join(stts_allergy)
        cursor.execute("UPDATE page_items SET Allergy_extraction='%s' WHERE ranks='%d'" % (string_allergy, ranks))
        print(string_allergy)


    conn.commit()  # 커밋 후
    conn.close  # 연결 종료
    #make_tts()
    return 0


#################################################################################################################################

def make_tts():
    #1. start 함수 실행 후 DB에 있는 내용으로 tts 텍스트와 음성파일 제작
    # +) 만약 DB에 내용이 있다면 이 함수만 단독으로 사용해도 된다.
    # +) 개수설정을 걸어놨으니 if문의 i를 잘 설정하자.

    conn = pymysql.connect(
        user=user,
        passwd=passwd,
        host=host,
        db=db
    )
    cursor = conn.cursor()
    sql = "SELECT * FROM test_db.page_items;"
    cursor.execute(sql)
    result = cursor.fetchall()

    stts = []
    i=0
    for re in result:

        product_rank = re[0]
        product_name = re[1]
        product_price = re[2]
        product_allergy = re[-1]
        #print(f"{product_rank}번 제품의 이름은 {product_name}입니다. 가격은 {product_price}입니다. 알러지정보는 {product_allergy}입니다.")
        text = f"{product_rank}번 제품의 이름은 {product_name} 입니다. 가격은 {product_price}원 입니다. 알러지정보는 {product_allergy}입니다."
        #print(text)
        stts.append(text)
        i+=1
        SttAndTts.make_audio(product_rank,text)
        if(i==10):
            #보고싶은 개수만 설정
            break
    conn.commit()  # 커밋 후
    conn.close  # 연결 종료

def replace_string(all):
    specialchars = "{}[](),/:을"

    for i in specialchars:
        # print(i)
        for a in range(len(all)):
            if (all[a] == i):
                all = all.replace(i, ' ')
    return all


def string_pre(all):
    new_all = []
    for a in range(len(all)):
        # 특수문자 처리
        all[a] = replace_string(all[a])

        # 포함제거
        poham = all[a].find("포함")
        if (poham != -1):
            all[a] = ''

        split_point = 0
        sp_str = all[a].split(" ")
        split_point += len(sp_str)

        for i in range(len(sp_str)):
            new_all.append(sp_str[i])

    new_all = list(filter(None, new_all))

    return new_all


def find_fac(all):
    fac_keyword = ['사용', '제품', '같은', '시설', '제조']
    fac_index = []
    for a in range(len(all)):
        for f in fac_keyword:
            if (all[a].find(f) != -1):
                fac_index.append(a)
    fac_index.sort()
    return fac_index


def find_facnum(fac_index):
    f = 0
    point = 0
    for i in range(len(fac_index) - 1):
        if (fac_index[i + 1] - fac_index[i] < 2):
            if (point == 0):
                f = fac_index[i]
            point += 1
            if (point >= 3):
                return f
        else:
            f = 0
            point = 0
    return -1


def find_index(all, keyword):
    index = []
    keys = []
    for a in range(len(all)):
        for k in keyword:
            num = all[a].find(k)
            if (num != -1):
                all[a] = k
                index.append(a)
                break
    index.sort()
    return index


def remove_fac(pre_re, food_index, fac_num):
    if (fac_num == -1):
        new_food_index = []
        new_food_index.append(food_index)
        return new_food_index
    food_index.append(fac_num)
    food_index.sort()
    f = fac_num
    fac = food_index.index(fac_num)
    for i in reversed(food_index[:fac]):
        if (f - i <= 2):
            f = i
        else:
            break

    new_food_index = []
    new_food_index.append(food_index[:food_index.index(f)])

    if (len(food_index) - 1 > food_index.index(fac_num)):
        new_food_index.append(food_index[food_index.index(fac_num):])
    return new_food_index


def stt_string(pre_re, allergy):
    stt = ""
    # print(f"<{name}>의 알러지유발성분 입니다.")
    set_allergy = []
    for a in allergy:
        for i in a:
            set_allergy.append(pre_re[i])
    result = set(set_allergy)
    for a in result:
        stt += a
        stt += ", "
        # print(a,end=' ')
    # print("입니다.")
    return stt


def find_allergy(re):
    keyword = ['메밀', '밀', '대두', '복숭아', '토마토', '우유', '치즈', '굴', '가리비', '전복', '홍합', '땅콩', '계란', '달걀', '고등어', '멸치', '명태',
               '가자미', '명태', '장어', '대구', '참치', '연어', '랍스터', '오징어', '게', '새우', '양고기', '소고기', '돼지고기', '아황산포함식품', '번데기',
               '닭고기', '쇠고기', '오징어', '잣', '오이', '토마토', '당근', '셀러리', '감자', '마늘', '양파', '딸기', '키위', '망고', '바나나', '감귤',
               '사과', '복숭아', '밤', '보리', '옥수수', '쌀', '밀가루', '참깨', '땅콩', '콩', '헤이즐럿', '호두', '카카오', '아모든', '해바라기씨', 'CCD항원',
               '효모', '올리브', '아카시아', '쑥'
                                    '난류', '알류', '견과류', '육류', '갑각류', '조개류', '아황산류']
    ite = 0
    stts = []
    for i in re:
        # print(f"--------------{name_list[ite]}-----------------")
        pre_re = string_pre(i)
        food_index = find_index(pre_re, keyword)
        fac_index = find_fac(pre_re)
        fac_num = find_facnum(fac_index)
        allergy = remove_fac(pre_re, food_index, fac_num)
        stt = stt_string(pre_re, allergy)
        stts.append(stt)
        ite += 1
    return stts


def naver_clova(src_link):
    re = []

    path = "/Users/leechanho8511/PycharmProjects/ssu_merge/images/tmp.png" #위치 수정
    urllib.request.urlretrieve(src_link, path)

    files = [('file', open(path, 'rb'))]

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

    all = []
    for field in result['images'][0]['fields']:
        text = field['inferText']
        all.append(text)
    re.append(all)

    return re

# allergy 정보 to DB ?????