
import matplotlib.pyplot as plt
from investar import Analyzer
import numpy as np
import pandas as pd
mk = Analyzer.MarketDB()
stocks = ['삼성전자','SK하이닉스','현대자동차','NAVER']
df = pd.DataFrame()
for s in stocks:
    df[s] = mk.get_daily_price(s)['close']
    print(s)

daily_ret = df.pct_change() #pandas 에서 제공하는 pct_change()함수로 4종목의 일간변동률을 구한다
annual_ret = daily_ret.mean() * 252 #일간변동률의 평균값에 252를 곱해서 연간수익률을 구한다.252는 미국의 1년 평균개장일
daily_cov = daily_ret.cov() #일간리스크는 cov()함수로 일간변동률의 공분산으로 구한다
annual_cov = daily_cov * 252 #연간공분산은 일간 공분산에 252를 곱해구한다
# print(annual_ret)

port_ret = []
port_risk = [] 
port_weights = []
# print(annual_ret)

#포트폴리오 2000개 생성, -변수에 할당
for _ in range(20000): 
     #4개의 랜덤숫자로 구성된 배열생성.
    weights = np.random.random(len(stocks))
    #위에서 구한 4개의 랜덤숫자를 랜덤숫자의 총합으로 나눠 4종목의 비중의합이 1이되도록
    weights /= np.sum(weights) 

    #랜덤하게 생성한 종목별 비중배열과 종목별 연간수익률을 곱해 해당포트폴리오 전체 수익률을 구한다
    returns = np.dot(weights, annual_ret) 

    #종목별 연간공분산과 종목별 비중배열을 곱한뒤 이를 다시 종목별 비중의 전치로 곱한다
    #이렇게 구한 결과값의 제곱근을 sqrt()함수로 구하며 해당포트폴리오 전체 리스크를 구할수 있다
    risk = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights)))

    #포트폴리오 20000개 수익률,리스크, 종목별 비중을 각각 리스트에 추가한다
    port_ret.append(returns)
    port_risk.append(risk)
    port_weights.append(weights)
    
  
portfolio = {'Returns':port_ret, 'Risk':port_risk}    

# print('portfolio 딕셔너리:',portfolio)
#i값은 0,1,2,3 순으로 변한다.이때 s값은 '삼성전자','SK하이닉스','현대자동차','NAVER'순으로 변한다
for i, s in enumerate(stocks):
    portfolio[s] = [weight[i] for weight in port_weights] #portfolio딕셔너리에 위회사순으로 비중값추가
    print(i, s)
    # print(portfolio[s])
    # print(port_weights)
df = pd.DataFrame(portfolio)
# print(df)
df = df[['Returns', 'Risk'] + [s for s in stocks]]
# print('데이터프레임:',df)
# print(df)


df.plot.scatter(x='Risk', y='Returns', figsize=(10,7), grid=True)
plt.title('Efficient Frontier')
plt.xlabel('Risk')
plt.ylabel('Expected Returns')
plt.show()
