from datetime import datetime
import backtrader as bt

class MyStrategy(bt.Strategy): #1.bt.Strategy 클래스를 상속받아서 MyStrategy 클래스를 작성한다
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close) #2.RSI지표를 사용하려면 MyStrategy 클래스 생성자에서 RSI지표로 사용할 변수를 지정한다
    def next(self): #3.next()메서드는 주어진 데이터와 지표(indicator)를 만족시키는 최소 주기마다 자동으로 호출된다.
                    #시장에 참여하고 있지 않을때 RSI가 30미만이면 매수하고, 시장에 참여하고 있을때 RSI가 70을 초과하면 매도하도록 구현
        if not self.position:
            if self.rsi < 30:
                self.order = self.buy()
        else:
            if self.rsi > 70:
                self.order = self.sell()

cerebro = bt.Cerebro() #4.Cerebro 클래스는 백트레이더의 핵심 클래스로서, 데이터를 취합하고 백테스트 또는 라이브 트레이딩을 실행 후
                       #그 결과를 출력하는 기능 담당
cerebro.addstrategy(MyStrategy)
data = bt.feeds.YahooFinanceData(dataname='036570.KS', #5. 엔씨소프트의 종가 데이터는 야후파이낸스 데이터를 통해 취합한다 
   fromdate=datetime(2017,1,1), todate=datetime(2019,12,1))
cerebro.adddata(data)
cerebro.broker.setcash(10000000) #6.초기 투자자금을 천만원으로 설정
cerebro.addsizer(bt.sizers.SizerFix, stake=30) #7.엔씨소프트의 주식의 매매단위는 30주로 설정.보유한 현금에 비해
                                               #매수하려는 주식의 총매수 금액(주가*매매 단위)이 크면 매수가 이루어지지 않음

print(f'Initial Portfolio Value : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.run() #8.cerbro클래스로 백테스트를 실행
print(f'Final Portfolio Value   : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.plot() #9.백테스트 결과 차트로 출력