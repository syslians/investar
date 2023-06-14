import pandas as pd
import matplotlib.pyplot as plt
import datetime
# from mplfinance import candlestick_ohlc
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from investar import Analyzer

mk = Analyzer.MarketDB()
df = mk.get_daily_price('엔씨소프트', '2017-01-01')

ema60 = df.close.ewm(span=60).mean()
ema130 = df.close.ewm(span=130).mean() 
macd = ema60 - ema130
signal = macd.ewm(span=45).mean() 
macdhist = macd - signal
df = df.assign(ema130=ema130, ema60=ema60, macd=macd, signal=signal,
    macdhist=macdhist).dropna()

df['number'] = df.index.map(mdates.date2num)
ohlc = df[['number','open','high','low','close']]

ndays_high = df.high.rolling(window=14, min_periods=1).max()      # ①14일동안의 최대값을 구한다.min_periods=1을 지정할경우,14일 기간에 해당하는 데이터가 모두
                                                                  #누적되지 않았더라도 최소 기간인 1일이상의 데이터만 존재하면 최대값을 구하라는 의미이다
ndays_low = df.low.rolling(window=14, min_periods=1).min()        # ②//최소값을 구하라는 의미이다
fast_k = (df.close - ndays_low) / (ndays_high - ndays_low) * 100  # ③빠른선%K를 구한다
slow_d= fast_k.rolling(window=3).mean()                           # ④3일 동안%K의 평균을 구해서 느린선%D에 저장한다
df = df.assign(fast_k=fast_k, slow_d=slow_d).dropna()             # ⑤%K와%D로 데이터프레임을 생성한뒤 결측치는 제거한다

plt.figure(figsize=(9, 7))
p1 = plt.subplot(2, 1, 1)
plt.title('Triple Screen Trading - Second Screen (NCSOFT)')
plt.grid(True)
candlestick_ohlc(p1, ohlc.values, width=.6, colorup='red', colordown='blue')
p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.plot(df.number, df['ema130'], color='c', label='EMA130')
plt.legend(loc='best')
p1 = plt.subplot(2, 1, 2)
plt.grid(True)
p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.plot(df.number, df['fast_k'], color='c', label='%K')
plt.plot(df.number, df['slow_d'], color='k', label='%D')
plt.yticks([0, 20, 80, 100]) # ⑥y축 눈금을 0,20,80,100으로 설정하여 스토캐스틱의 기준선을 나타낸다
plt.legend(loc='best')
plt.show()
