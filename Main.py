import time
import csv
from datetime import datetime
import math
import ccxt

bitmex = ccxt.bitmex({
    'apiKey': 'JMc535WFmvHM8EOZEILAOQLv',
    'secret': '6gp-75qNx3cjKbTgsOqrCe-hJnau52F143MH5vAY4v1v3XKO',
    'enableRateLimit': True,
})

data = []
# 초기값(현재 상태) 설정(실행 전 입력할 것.) 하단에 예시
# data = [side, amount] side = str, amount = int
# data = ['buy', 340]
# data = ['sell', 200]

lev = 3  # leverage
bitmex.private_post_position_leverage({"symbol": "XBTUSD", "leverage": str(lev)})

def WMA(df, period): # 가중이동평균
    result = []
    for epoch in range(len(df) - period+1):
        value = 0
        for n in range(1, period+1):
            value = value + (df[n+epoch-1] * n)
        result.append(value / ((period * (period + 1)) / 2))
    return result

def HMA(df, period): # Hull 이동평균
    data1 = WMA(df, int(period/2))
    for i in range(0, len(data1)):
        data1[i] = data1[i] * 2
    data2 = WMA(df, period)
    data3 = []
    for i in range(0, len(data2)):
        data3.append(data1[i + len(data1) - len(data2)] - data2[i])
    return (WMA(data3, int(math.sqrt(period))))

def Order(side, Unit):
    make_order = bitmex.create_order('BTC/USD', 'limit', side , Unit , (bitmex.fetch_ticker('BTC/USD')['close']))
    data.clear()
    data.append(side)
    data.append(int(make_order['amount']))

while(True):
    now = datetime.now()
    reset_time = ('%s' % (now.hour))
    if reset_time != 0:
        #print('Not Yet...')
        time.sleep(3)
        continue
    
    time.sleep(60)

    timestamp = datetime.datetime.now().timestamp()
    datetimeobj = str(datetime.datetime.fromtimestamp(timestamp-8553600))
    start = datetimeobj[0:10] + 'T' + '00:00:00'
    XBT_ohlcv = bitmex.fetch_ohlcv('BTC/USD', "1d",bitmex.parse8601(start))
    XBT = []

    for i in range(0, 100):
        XBT.append(XBT_ohlcv[i][4])

    period13 = HMA(XBT, 13)
    period52 = HMA(XBT, 52)

    Input_money = 0.99 * (bitmex.fetch_balance()['BTC']['free'])
    Contract_num_BTCUSD = int(3 * Input_money * (bitmex.fetch_ticker('BTC/USD')['close']))

    if not data:
        if (period13[-1] < period13[-2]) and (period52[-1] < period52[-2]):
            Order('sell', Contract_num_BTCUSD) 
        elif (period13[-1] > period13[-2]) and (period52[-1] > period52[-2]):
            Order('buy', Contract_num_BTCUSD)
    else:
        if data[0] == 'buy' and (period13[-1] < period13[-2]):
            Order('sell', data[1])
        elif data[0] == 'sell' and (period13[-1] > period13[-2]):
            Order('buy', data[1])
    time.sleep(3600)
