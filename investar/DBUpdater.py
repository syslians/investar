import pymysql
import pandas as pd
from datetime import datetime
import ssl
from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import calendar
import threading
import schedule
import time
from selenium import webdriver
import requests

class DBUpdater:
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host='localhost',
                                    user='root',
                                    password='gu56417974!',
                                    database='investar',
                                    charset='utf8'                                    
                                    )
        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code)
                )
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price(
                code VARCHAR(20),
                date DATE,
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                diff BIGINT(20),
                volume BIGINT(20),
                PRIMARY KEY (code, date)
            )
            """
            curs.execute(sql)
        self.conn.commit()
        

        self.codes = dict()
        self.update_comp_info()  

    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close()
     
    def read_krx_code(self):
        """KRX로부터 상장기업 목록 파일을 읽어와서 데이터레임으로 반환"""
        ssl._create_default_https_context = ssl._create_unverified_context
        url = 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        krx = pd.read_html(url, header=0)[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드':'code','회사명':'company'})
        krx.code = krx.code.map('{:06d}'.format)
        
        return krx
        print("krx 데이터프레임:", krx)

    def update_comp_info(self):
        """종목코드를 company_info 테이블로 업데이트 후 딕셔너리에 저장"""
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn) #company_info 테이블에서 자료를 읽어와 데이터프레임에 저장
        print("read_sql = ",df)
    
        for idx in range(len(df)):            
            self.codes[df['code'].values[idx]]=df['company'].values[idx]
            # print("company_info 테이블:", self.codes)
            
        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            print("rs:",rs[0])
            today = datetime.today().strftime('%Y-%m-%d')
            print("오늘 연 월 일:",today)

            #rs[0] = 2023-01-25(오늘날짜)가 없거나 오늘날짜보다 작다면
            #업데이트 되어있으면 코드실행X
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                krx = self.read_krx_code()
                for idx in range(len(krx)):
                    code = krx.code.values[idx]
                    company = krx.company.values[idx]
                    sql = f"REPLACE INTO company_info (code, company, last"\
                        f"_update) VALUES ('{code}', '{company}', '{today}')"
                    curs.execute(sql)
                    self.codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}],{idx:04d} REPLACE INTO company_info"\
                        f"VALUES ({code}, {company}, {today}")
                self.conn.commit()
                print('')
            

    def read_naver(self, code, company, pages_to_fetch):
        """네이버 금융에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            url = f"http://finance.naver.com/item/sise_day.nhn?code={code}"
            headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}
            req = requests.get(url, headers=headers)
            html = BeautifulSoup(req.text , "lxml")
            # print("파싱된소스:", html)
            pgrr = html.select_one('td.pgRR').a['href']
            table = (html.select_one('table.type2'))
            stable = str(table)           

            if pgrr is None:
                return None
            lastpage = pgrr.split('=')[-1]
            
            df = pd.DataFrame()

            pages = min(int(lastpage), pages_to_fetch)

            for page in range(1, pages + 1):
                
                req1 = requests.get(f'{url}&page={page}', headers=headers)                    
                
                df = pd.concat([df,pd.read_html(req1.text, encoding='euc-kr')[0]])
                print(df)
             
                df.dropna(axis='index', how='all', inplace=True)
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')

                print('[{}] {} ({}) : {:04d}/{:04d} page are downloading...'.format(
                    tmnow, company, code, page, pages))
                # print(df)
            df = df.rename(columns={'날짜':'date','종가':'close','전일비':'diff','시가':'open',
                '고가':'high','저가':'low','거래량':'volume'})
                # print('바뀐 데이프레임:', df)
                #4.연.월.일 의 날짜 형식을 연-월-일 형식으로 바꾼다
            df['date'] = df['date'].replace('.', '-')
                
                #5.마리아디비에서 BIGINT형으로 지정한 컬럼들을 int형으로 변경
            df[['close','diff','open','high','low','volume']] = df[['close',
                    'diff','open','high','low','volume']].astype(int)
                #6.원하는 순서로 컬럼을 재조합하여 데이터프레임을 만든다
            df = df[['date','open','high','low','close','diff','volume']]
            print('진짜 바뀐 데이터프레임:',df)
         
        except Exception as e:
            print('Exception occured :', str(e))
            return None
        return df

    def replace_into_db(self, df, num, code, company):
        """네이버 금융에서 읽어온 주식시세를 DB에 REPLACE"""
        with self.conn.cursor() as curs:
            #1.인수로 넘겨받은 데이터를 튜플로 순회처리시킨다
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{code}', "\
                      f"'{r.date}', {r.open}, {r.high}, {r.low}, {r.close}, "\
                      f"{r.diff}, {r.volume})"
                #2.REPLACE INTO 구문으로 daily_price 테이블을 업데이트한다
                curs.execute(sql)
            self.conn.commit()
            print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_'\
            'price [OK]'.format(datetime.now().strftime('%Y-%m-%d'\
            ' %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식시세를 네이버로부터 읽어서 DB에 업데이트"""
        #1.self.codes 딕셔너리{'code':,'company'}에 저장된 모든 종목코드에 대해 순회처리
        #code에 위 딕셔너리가 담긴다
        for idx, code in enumerate(self.codes):
            print('종목코드:',code)
            print('회사명:',self.codes[code])
            #2.read_naver() 메서드로 종목코드에 대한 일별시세 데이터프레임을 구한다
            #read_naver({'종목코드', '회사명', 'pages_to_fetch' )
            df = self.read_naver(code, self.codes[code], pages_to_fetch)
            
            if df is None:
                continue
            
            #3.일별시세 데이터프레임이 구해지면 replace_into()메서드로 DB에 저장
            self.replace_into_db(df, idx, code, self.codes[code])

    def execute_daily(self):
        """실행 즉시 및 매일 오후 다섯시에 daily_price 테이블 업데이트"""
        #1.update_comp_info()메서드를 호출해서 상장법인 목록을 DB에 업데이트
        self.update_comp_info()
        try:
            #2.DBUpdater.py가 있는 디렉터리에서 config.json 파일을 읽기모드로 연다
            with open('config.json', 'r') as in_file:
                config = json.load(in_file)
                #3.파일이 있다면 pages_to_fetch값을 읽어서 프로그램에서 사용한다
                pages_to_fetch = config['pages_to_fetch']
                #4.1에서 열려고 했던 config.json파일이 존재하지 않을경우
        except FileNotFoundError:
            with open('config.json', 'w') as out_file:
                #5.최초 실행시 프로그램에서 사용할 page_to_fetch값을 100으로 설정한다
                #config.json 파일에 page_to_fetch값을 1로 저장해서 이후부터는 1페이지씩 읽음
                pages_to_fetch = 1
                config = {'pages_to_fetch': 1}
                json.dump(config, out_file)
                #6.pages_to_fetch값으로 update_daily_price() 메서드를 호출
        self.update_daily_price(pages_to_fetch)

        tmnow = datetime.now()
        #7.이번달의 마지막날을 구해 다음날 오후5시를 계산하는데 사용한다
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1,
               minute=0, second=0)
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17,
            minute=0, second=0)
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17,
               minute=0, second=0)
        tmdiff = tmnext - tmnow
        secs = tmdiff.seconds
        print("tmnow:", tmnow)
        print("tmnext:", tmnext)
        print("tmdiff:", tmdiff)
        print("secs:",secs)
        # t = self.execute_daily()

        # 8.다음날 오후 5시에 execute_daily()메서드를 실행하는 Timer 객체를 생성한다
        t = threading.Timer(secs, self.execute_daily)
        # schedule.every().day.at("17:00").t()
        print("waiting for next update ({}) ...".format(tmnext.strftime
             ('%Y-%m-%d %H:%M')))
        print(datetime.now())
        t.start()
    

if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.execute_daily()
      