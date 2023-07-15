#!/usr/bin/env python
# coding: utf-8

# In[6]:


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
#from selenium.webdriver import ActionChains
# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time


query_txt = input('검색할 키워드 : ')

# 크롬드라이버 실행
driver = webdriver.Chrome()

#크롬 드라이버에 url 주소 넣고 실행
HomeUrl="https://front.homeplus.co.kr/"
GooUrl = "https://www.google.co.kr/"
driver.get(HomeUrl)

# 페이지가 완전히 로딩되도록 3초동안 기다림
time.sleep(3)

# 검색창에 키워드 입력 후 검색
driver.find_element(By.NAME, "keyword").send_keys(query_txt, Keys.ENTER) 


# In[7]:


import MySQLdb

time.sleep(5) # 안걸어주면 한줄당 3개의 상품들만 출력됨

conn = MySQLdb.connect(
    user="crawl_usr",
    passwd="test1",
    host="localhost",
    db="homeplus"
)

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
    
    print(name)
    print(price)
    print(link)
    
    cursor.execute("INSERT INTO page_items VALUES (%d, '%s', '%s', '%s')"%(ranks, name, price, link))
    ranks += 1
    
    
# 커밋
conn.commit()
# 연결 종료
conn.close

# items = [item for item in zip(name_list, price_list, link_list)]
    
# name_list.append(prod.find_element(By.CLASS_NAME, "css-12cdo53-defaultStyle-Typography-ellips").text)
# price_list.append(prod.find_element(By.CLASS_NAME, "priceValue").text)
# link_list.append(prod.find_element(By.CLASS_NAME, "productTitle").get_attribute('href'))  

# print(name_list)
# print(price_list)
# print(link_list)


# In[14]:






# 테이블 생성
cursor.execute("CREATE TABLE page_items ('rank' int, name text, price int, url text)")

i = 1
for item in items :
    cursor.execute(
        f"INSERT INTO page_items VALUES({I},\"{item[0]}\",\"{item[1]}\",\"{item[2]}\")")
    i += 1


# In[28]:





# In[ ]:


for name in product_name[:5] :
    p_name = name.text
    p_name = p_name.replace('\n', '')
    p_name = p_name.replace(' ', '')
    p_name = p_name.replace(',', '')
    product_names.append(p_name)
    
for name in product_price[:5] :
    p_price = price.text
    p_price = p_price.replace(',', "")
    product_prices.append(p_price)
    
for link in product_link[:5] :
    p_link = "https://front.homeplus.co.kr" + link['href']
    product_links.append(p_link)
    
print(product_names)


# In[116]:





# In[100]:


# 영양정보 이미지 위치로 이동
driver.execute_script("window.scrollTo(0, 3000)") 
time.sleep(5)

imgs = driver.find_element(By.CLASS_NAME,"prodDetailArea").find_elements(By.TAG_NAME,'img')

results = []
for img in imgs:
    link = img.get_attribute('src')
    print(link)


# In[ ]:




