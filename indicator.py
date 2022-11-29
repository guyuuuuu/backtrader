import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

import pandas as pd
import datetime

import matplotlib.pyplot as plt

plt.style.use('seaborn') # 使用 seaborn 主题
plt.rcParams['figure.figsize'] = 20, 10  # 全局修改图大小

# 修改 Trades 观测器的样式
class my_Trades(bt.observers.Trades):
    plotlines = dict(
    pnlplus=dict(_name='Positive',
                 marker='^', color='#ed665d',
                 markersize=8.0, fillstyle='full'),
    pnlminus=dict(_name='Negative',
                  marker='v', color='#729ece',
                  markersize=8.0, fillstyle='full'))

# 修改 BuySell 的样式
class my_BuySell(bt.observers.BuySell):
    
    params = (('barplot', True), ('bardist', 0.02))
    
    plotlines = dict(
    buy=dict(marker=r'$\Uparrow$', markersize=10.0, color='#d62728' ),
    sell=dict(marker=r'$\Downarrow$', markersize=10.0, color='#2ca02c'))
    

data = pd.read_csv('AAPL.csv')

data.set_index('Date', inplace = True)
data.columns = [i.lower() for i in data.columns]
data['close'] = data['adj close']
data = data.drop(['adj close'], axis = 1)
data['openinterest'] = 0
data.index = pd.to_datetime(data.index)
data = data.loc[datetime.datetime(2015,1,1):,:]
start_date = data.index[0]
end_date = data.index[-1]

class PandasData_more(bt.feeds.PandasData):
    lines = ('pe', 'pb', ) # 要添加的线
    # 设置 line 在数据源上的列位置
    params=(
        ('pe', -1),
        ('pb', -1),
           )

# 实例化 cerebro
cerebro = bt.Cerebro(stdstats=False)
datafeed = PandasData_more(dataname = data, fromdate = start_date, todate = end_date)
cerebro.adddata(datafeed, name = 'AAPL')

# 通过经纪商设置初始资金
cerebro.broker.setcash(10000000)
# 设置交易佣金
cerebro.broker.setcommission(commission=0.0003)
cerebro.broker.set_slippage_perc(perc = 0.0001)

class strategy(bt.Strategy):
    def __init__(self):
        # 打印数据集和数据集对应的名称
        print("-------------self.datas-------------")
        print(self.datas)
        print("-------------self.data-------------")
        print(self.data._name, self.data) # 返回第一个导入的数据表格，缩写形式
        print("-------------self.data0-------------")
        print(self.data0._name, self.data0) # 返回第一个导入的数据表格，缩写形式
        print("-------------self.datas[0]-------------")
        print(self.datas[0]._name, self.datas[0]) # 返回第一个导入的数据表格，常规形式
        sma = bt.indicators.SMA(self.datas[0].close)
        print(sma.lines[0])

        print("0 索引：",'datetime',self.data0.lines.datetime.date(0), 'close',self.data0.lines.close[0])
        print("-1 索引：",'datetime',self.data0.lines.datetime.date(-1),'close', self.data0.lines.close[-1])
        print("-2 索引",'datetime', self.data0.lines.datetime.date(-2),'close', self.data0.lines.close[-2])
        print("1 索引：",'datetime',self.data0.lines.datetime.date(1),'close', self.data0.lines.close[1])
        print("2 索引",'datetime', self.data0.lines.datetime.date(2),'close', self.data0.lines.close[2])
        print("从 0 开始往前取3天的收盘价:", self.data0.lines.close.get(ago=0, size=3))
        print("从-1开始往前取3天的收盘价:", self.data0.lines.close.get(ago=-1, size=3))
        print("从-2开始往前取3天的收盘价:", self.data0.lines.close.get(ago=-2, size=3))
        print("line的总长度:", self.data0.buflen())

        print(self.data0.lines.getlinealiases())

        sma1 = btind.SimpleMovingAverage(self.data)
        ema1 = btind.ExponentialMovingAverage(self.data)
        close_over_sma = self.data.close > sma1
        close_over_ema = self.data.close > ema1
        sma_ema_diff = sma1 - ema1
        self.buy_sig = bt.And(close_over_sma, close_over_ema, sma_ema_diff > 0)

    def log(self, txt, dt=None):
        '''可选，构建策略打印日志的函数：可用于打印订单记录或交易记录等'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 未被处理的订单
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 已经处理的订单
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            if order.isbuy():
                self.log('BUY EXECUTED, ref:%.0f, Price: %.2f, Cost: %.2f, Comm %.2f, Size: %.2f, Stock: %s' %
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

    def next(self):
        if self.buy_sig:
            self.buy()
        pass

# 添加策略
cerebro.addstrategy(strategy)
# 添加观测器
cerebro.addobserver(bt.observers.DrawDown)
cerebro.addobserver(bt.observers.Broker)
cerebro.addobserver(my_Trades)
cerebro.addobserver(my_BuySell)
# 添加策略分析指标
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 年化收益率
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio') # 夏普比率
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 回撤

# 启动回测
result = cerebro.run()
strat = result[0]
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())

#策略运行完后，绘制图形
colors = ['#729ece', '#ff9e4a', '#67bf5c', '#ed665d', '#ad8bc9', '#a8786e', '#ed97ca', '#a2a2a2', '#cdcc5d', '#6dccda']
tab10_index = [3, 0, 2, 1, 2, 4, 5, 6, 7, 8, 9]
cerebro.plot(iplot=False,
              style='line', # 绘制线型价格走势，可改为 'candel' 样式
              lcolors=colors,
              plotdist=0.1,
              bartrans=0.2,
              volup='#ff9896',
              voldown='#98df8a',
              loc='#5f5a41',
              numfigs=2) # 删除水平网格

# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers._AnnualReturn.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers._SharpeRatio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers._DrawDown.get_analysis())


# 提取收益序列
pnl = pd.Series(result[0].analyzers.pnl.get_analysis())
# 计算累计收益
cumulative = (pnl + 1).cumprod()
# 计算回撤序列
max_return = cumulative.cummax()
drawdown = (cumulative - max_return) / max_return
# 计算收益评价指标
import pyfolio as pf
# 按年统计收益指标
perf_stats_year = (pnl).groupby(pnl.index.to_period('y')).apply(lambda data: pf.timeseries.perf_stats(data)).unstack()
# 统计所有时间段的收益指标
perf_stats_all = pf.timeseries.perf_stats((pnl)).to_frame(name='all')
perf_stats = pd.concat([perf_stats_year, perf_stats_all.T], axis=0)
perf_stats_ = round(perf_stats,4).reset_index()


# 绘制图形
import matplotlib.pyplot as plt
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
import matplotlib.ticker as ticker # 导入设置坐标轴的模块
plt.style.use('dark_background')

fig, (ax0, ax1) = plt.subplots(2,1, gridspec_kw = {'height_ratios':[1.5, 4]}, figsize=(20,8))
cols_names = ['date', 'Annual\nreturn', 'Cumulative\nreturns', 'Annual\nvolatility',
       'Sharpe\nratio', 'Calmar\nratio', 'Stability', 'Max\ndrawdown',
       'Omega\nratio', 'Sortino\nratio', 'Skew', 'Kurtosis', 'Tail\nratio',
       'Daily value\nat risk']

# 绘制表格
ax0.set_axis_off() # 除去坐标轴
table = ax0.table(cellText = perf_stats_.values,
                bbox=(0,0,1,1), # 设置表格位置， (x0, y0, width, height)
                rowLoc = 'right', # 行标题居中
                cellLoc='right' ,
                colLabels = cols_names, # 设置列标题
                colLoc = 'right', # 列标题居中
                edges = 'open' # 不显示表格边框
                )
table.set_fontsize(13)

# 绘制累计收益曲线
ax2 = ax1.twinx()
ax1.yaxis.set_ticks_position('right') # 将回撤曲线的 y 轴移至右侧
ax2.yaxis.set_ticks_position('left') # 将累计收益曲线的 y 轴移至左侧
# 绘制回撤曲线
drawdown.plot.area(ax=ax1, label='drawdown (right)', rot=0, alpha=0.3, fontsize=13, grid=False)
# 绘制累计收益曲线
(cumulative).plot(ax=ax2, color='#F1C40F' , lw=3.0, label='cumret (left)', rot=0, fontsize=13, grid=False)
# 不然 x 轴留有空白
ax2.set_xbound(lower=cumulative.index.min(), upper=cumulative.index.max())
# 主轴定位器：每 5 个月显示一个日期：根据具体天数来做排版
ax2.xaxis.set_major_locator(ticker.MultipleLocator(100))
# 同时绘制双轴的图例
h1,l1 = ax1.get_legend_handles_labels()
h2,l2 = ax2.get_legend_handles_labels()
plt.legend(h1+h2,l1+l2, fontsize=12, loc='upper left', ncol=1)

fig.tight_layout() # 规整排版
plt.show()