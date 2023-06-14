import matplotlib.pyplot as plt
from investar import Analyzer

mk = Analyzer.MarketDB()
df = mk.get_daily_price('NAVER','2019-01-01','2019-11-11')
  
# 20개 종가를 이용해서 평균을 구한다
df['MA20'] = df['close'].rolling(window=20).mean() 
# 20개 종가를 이용해서 표준편차를 구한뒤 stdev 컬럼으로 df에 추가한다
df['stddev'] = df['close'].rolling(window=20).std() 
# 상단 볼린저 밴드 계산
df['upper'] = df['MA20'] + (df['stddev'] * 2)
#하단 볼린저 밴드 계산
df['lower'] = df['MA20'] - (df['stddev'] * 2)
df['PB'] = (df['close'] - df['lower']) / (df['upper'] - df['lower'])
#고가,저가,종가의 합을 3으로 나눠서 중심가격 TP를 구한다
df['TP'] = (df['high'] + df['low'] + df['close']) / 3
df['PMF'] = 0
df['NMF'] = 0
#i번째 중심가격보다 i+1번째 중심가격이 높으면 i+1번째 중심가격과 i+1번째 거래량의 곱을 
#i+1번째 긍정적 현금흐름 PMF에 저장한다
for i in range(len(df.close)-1):
    if df.TP.values[i] < df.TP.values[i+1]:
        df.PMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
        df.NMF.values[i+1] = 0 #i+1번째 부정적현금흐름NMF에 저장한다
    else:
        df.NMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
        df.PMF.values[i+1] = 0
df['MFR'] = (df.PMF.rolling(window=10).sum() /
    df.NMF.rolling(window=10).sum()) #10일동안의 현금흐름의 합을 10일동안이 부정적 현금흐름의 합으로 나눈 결과를MER 컬럼에 저장
df['MFI10'] = 100 - 100 / (1 + df['MFR']) #10일 기준으로 현금흐름지수를 계산한 결과를 MEF10컬럼에 저장
df = df[19:] # 19번째 행까지 NaN이므로 값이 있는 20번째 행부터 사용한다

plt.figure(figsize=(9, 8))
plt.subplot(2, 1, 1)
plt.title('NAVER Bollinger Band(20 day, 2 std) - Trend Following')
# x좌표 df.index에 해당하는 종가를 y좌표로 설정해 파란색 실선으로 표시
plt.plot(df.index, df['close'], color='#0000ff', label='Close')
# x좌표 df.index에 해당하는 상단 볼린저 밴드값을 y좌표로 설정해 검은 실선으로 표시
plt.plot(df.index, df['upper'], 'r--', label ='Upper band')
plt.plot(df.index, df['MA20'], 'k--', label='Moving average 20')
plt.plot(df.index, df['lower'], 'c--', label ='Lower band')
# 상단 볼린저밴드와 하단 볼린저 밴드 사이를 회색으로 칠한다
plt.fill_between(df.index, df['upper'], df['lower'], color='0.9')
for i in range(len(df.close)):
    if df.PB.values[i] > 0.8 and df.MFI10.values[i] > 80:       # ①%b가 0.8보다 크고 10일기준 MFI가 80보다 크면
        plt.plot(df.index.values[i], df.close.values[i], 'r^')  # ②매수시점을 나타내기 위해 첫번째 그래프의 종가위치에 빨간색 삼각형을 표시
    elif df.PB.values[i] < 0.2 and df.MFI10.values[i] < 20:     # ③%b가 0.2보다 작고 10일 기준 MFI가 20보다 작다면 
        plt.plot(df.index.values[i], df.close.values[i], 'bv')  # ④매도 시점을 나타내기 위해 첫번째 그래프의 종가위치에 파란색 삼각형 표시
plt.legend(loc='best')

plt.subplot(2, 1, 2)
plt.plot(df.index, df['PB'] * 100, 'b', label='%B x 100')       # ⑤ MFI와 비교할수 있게 %b를 그대로 표시하지 않고 100을 곱해 푸른색 실선으로 표시
plt.plot(df.index, df['MFI10'], 'g--', label='MFI(10 day)')     # ⑥10일기준 MFI를 녹색점선으로 표시
plt.yticks([-20, 0, 20, 40, 60, 80, 100, 120])                  # ⑦y축 눈금을 -20부터 120까지 20단위로 표시
for i in range(len(df.close)):
    if df.PB.values[i] > 0.8 and df.MFI10.values[i] > 80:
        plt.plot(df.index.values[i], 0, 'r^')
    elif df.PB.values[i] < 0.2 and df.MFI10.values[i] < 20:
        plt.plot(df.index.values[i], 0, 'bv')
plt.grid(True)
plt.legend(loc='best')
plt.show();   
