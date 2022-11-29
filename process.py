import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

import pandas as pd
import datetime

data = pd.read_csv('AAPL.csv')

data.set_index('Date', inplace = True)
data.columns = [i.lower() for i in data.columns]
data['close'] = data['adj close']
data = data.drop(['adj close'], axis = 1)
data['openinterest'] = 0
data.index = pd.to_datetime(data.index)
data = data.loc[datetime.datetime(2000,1,1):,:]
start_date = data.index[0]
end_date = data.index[-1]

# 实例化 cerebro
cerebro = bt.Cerebro()
datafeed = bt.feeds.PandasData(dataname = data, fromdate = start_date, todate = end_date)
cerebro.adddata(datafeed, name = 'AAPL')

# 通过经纪商设置初始资金
cerebro.broker.setcash(10000000)
# 设置交易佣金
cerebro.broker.setcommission(commission=0.0003)
cerebro.broker.set_slippage_perc(perc = 0.0001)

class TestStrategy(bt.Strategy):
    # 可选，设置回测的可变参数：如移动均线的周期
    params = (
        ('long',20),
        ('short', 5), # 最后一个“,”最好别删！
    )
    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        '''必选，初始化属性、计算指标等'''
        self.order = None
        self.dataclose = self.datas[0].close
        self.gold_cross = False
        self.death_cross = False
        
        self.sma_20 = bt.indicators.SMA(self.datas[0], period = 20)
        self.sma_5 = bt.indicators.SMA(self.datas[0], period = 5)


        pass

    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log(
                        'BUY EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                        (order.ref, # 订单编号
                        order.executed.price, # 成交价
                        order.executed.value, # 成交额
                        order.executed.comm, # 佣金
                        order.executed.size, # 成交量
                        order.data._name)) # 股票名称
            else: # Sell
                self.log('SELL EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
                            (order.ref,
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm,
                            order.executed.size,
                            order.data._name))
        pass


    def notify_trade(self, trade):
        '''可选，打印交易信息'''
        pass

    def next(self):
        '''必选，编写交易策略逻辑'''

        if self.sma_5 >= self.sma_20 and not self.gold_cross:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order_target_percent(target = 0.95)
            self.gold_cross = True
            self.death_cross = False
        
        if self.sma_5 <= self.sma_20 and not self.death_cross:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.sell()
            self.gold_cross = False
            self.death_cross = True
        
        pass

# 添加策略
cerebro.addstrategy(TestStrategy)
# 添加策略分析指标
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 年化收益率
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio') # 夏普比率
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 回撤
# 启动回测
result = cerebro.run()
strat = result[0]
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())

# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers._AnnualReturn.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers._SharpeRatio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers._DrawDown.get_analysis())

# 可视化回测结果
cerebro.plot()
