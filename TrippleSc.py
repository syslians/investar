import pandas as pd
import matplotlib.pyplot as plt
import datetime
# from mplfinance import candlestick_ohlc
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from investar import Analyzer

class TrippleScreen():

    def __init__(self,company, start_date):
        mk = Analyzer.MarketDB()
        self.df = mk.get_daily_price(company, start_date)
        self.company = company
        self.ohlc = pd.DataFrame()
    
    #첫번째 창 -시장조류분석
    def get_market_tide(self):
        df = self.df
        ema60 = df.close.ewm(span=60).mean() #종가의12주 이평선
        ema130 = df.close.ewm(span=130).mean() #종가의 26주 이평선
        macd = ema60 - ema130 #macd선
        signal = macd.ewm(span=45).mean() #시그널선
        macdhist = macd - signal #히스토그램

        #데이터프레임 컬럼에 추가
        df = df.assign(ema130=ema130, ema60 = ema60, macd = macd,
                           signal = signal, macdhist=macdhist).dropna()
        df['number'] = df.index.map(mdates.date2num)#만들어진 ohlc와 df를 각각 대응하는 멤버 변수에 저장
        ohlc = df[['number', 'open', 'high', 'low', 'close']]
        ohlc.index = pd.to_datetime(ohlc.index)
        self.ohlc = ohlc
        self.df = df
        return

    def show_candle_chart(self,subplot):
        df = self.df
        plt.title('Candle & MACD Chart')
        plt.grid(linestyle = "dotted")
        candlestick_ohlc(subplot, self.ohlc.values, width=.6, colorup='red', colordown='blue')
        subplot.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.plot(df.number, df['ema130'], color='c', label = 'EMA130')
        plt.legend(loc='best')

    def show_macd_chart(self, subplot):
        df = self.df
        subplot.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.bar(df.number, df['macdhist'], color='m', label='MACD-hist')
        plt.plot(df.number, df['macd'], color='b', label='MACD')
        plt.plot(df.number, df['signal'], 'g--', label='MACD-signal')
        plt.legend(loc='best')

    #두번째 창 -시장파도 분석
    def get_market_wave(self):
        df = self.df
        ndays_high = df.high.rolling(window=14, min_periods=1).max() #14일간의 최고가
        ndays_low = df.low.rolling(window=14, min_periods=1).min() #14일간의 최저가
        fast_k = (df.close - ndays_low) / (ndays_high - ndays_low) * 100 #빠른선 %K
        slow_d = fast_k.rolling(window=3).mean() #느린선 %D
        df = df.assign(fast_k=fast_k, slow_d=slow_d).dropna()
        self.df = df
        return
    
    def show_stochastic_chart(self, subplot):
        df = self.df
        subplot.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.plot(df.number, df['fast_k'], color ='c', label='%K')
        plt.plot(df.number, df['slow_d'], color = 'k', label='%D')
        plt.yticks([0, 20, 80, 100])
        plt.legend(loc='best')

    #세번째 창 -진입기술
    def sim_trade(self):
        account = 1000000
        stocks = 0
        profit = 0

        df = self.df
        for i in range(len(df.close)):
            #26주 ema가 상승하면서 %D선이 20 이상을 돌파하며
            #추락하면 매수 시그널
            if df.ema130.values[i-1] < df.ema130.values[i] and \
                df.slow_d.values[i-1] >= 20 and df.slow_d.values[i] < 20:
                print(df)
                # plt.plot(df.number.values[i],250000, 'r^')
                account -= df.close.values[i] #자산은 줄어들고
                stocks += 1 #주식은 늘어난다(1주씩)
                print(f"[{df.index.values[i]}] 매수 체결 - 매수가 : {df.close.values[i]} | "
                      f"체결 수량 : 1 | 현재 총 {stocks} 주")
                #26주 ema가 하락하면서 %D선이하로 돌파상승하면 매도 시그널
            elif df.ema130.values[i-1] > df.ema130.values[i] and \
                df.slow_d.values[i-1] <= 80 and df.slow_d.values[i] > 80:
                # plt.plot(df.number.values[i], 250000, 'bv')
                if stocks == 0: #보유한 주식이 없다면 지속
                    continue
                print(f"[{df.index.values[i]}] 매도 체결 - 매도가 : {df.close.values[i]} |"
                      f"체결 수량 : {stocks} | 현재 총 0 주")
                account += stocks * df.close.values[i]
                stocks = 0
        #총수익 = 매입한 주식의 총가치 + 실현손익
        profit = account + df.close.values[len(df.close)-1] * stocks - 1000000
        print(f"삼중창 매매법 총 수익 : {profit} (원)")

### main함수
plt.figure(figsize=(9, 9))
tw = TrippleScreen('금양','2022-03-06')
tw.get_market_tide() 
p1 = plt.subplot(3,1,1)
tw.show_candle_chart(p1)
p2 = plt.subplot(3,1,2)
tw.show_macd_chart(p2)
tw.get_market_wave()
p3 = plt.subplot(3,1,3)
tw.show_stochastic_chart(p3)
tw.sim_trade()
plt.show()  
