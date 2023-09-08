import pyupbit
import time
from collections import deque

CASH = 10000


class RealCoin(pyupbit.Upbit):
    def __init__(self, key0, key1):
        super().__init__(key0, key1)

    def get_current_price(self, ticker):
        while True:
            price = pyupbit.get_current_price(ticker)
            if price != None:
                return price
            else:
                print("get_current_price wait")
                time.sleep(0.2)

    def buy_market_order(self, ticker, cash):
        while True:
            order = super().buy_market_order(ticker, cash)
            # 정상적으로 처리되지 않는다면 반복 시도
            if order == None or "error" in order:
                print("buy_marker_order wait", ticker, cash, order)
                time.sleep(0.3)
                continue
            # 정상적으로 처리되었다면 완료
            else:
                return order

    def get_order_detail(self, uuid):
        while True:
            order = super().get_order(uuid)
            print(order)
            if order != None and len(order["trades"]) > 0:
                return order
            else:
                print("get_order_detail wait", uuid)
                time.sleep(0.2)

    def get_outstanding_order(self, ticker):
        while True:
            order = super().get_order(ticker)
            if order != None and len(order) == 0:
                return order
            else:
                print("get_outstanding_order wait", ticker)
                time.sleep(0.2)

    # 현금 조회
    def get_balance(self, ticker="KRW"):
        while True:
            volume = super().get_balance(ticker)
            if volume != None:
                return volume
            else:
                print("get_balance wait", ticker)
                time.sleep(0.2)

    def sell_limit_order(self, ticker, price, volume):
        price = pyupbit.get_tick_size(price)
        while True:
            order = super().sell_limit_order(ticker, price, volume)
            if order != None and "uuid" in order:
                return order
            else:
                print("sell_limit_order wait", price, volume, order)
                time.sleep(0.2)


class Real1Percent(RealCoin):
    def __init__(self, key0, key1, ticker):
        super().__init__(key0, key1)
        self.ticker = ticker

        # 이동평균선에 관한 과거 정보 Get
        self.ma15 = deque(maxlen=15)
        self.ma50 = deque(maxlen=50)
        self.ma120 = deque(maxlen=120)

        df = pyupbit.get_ohlcv(self.ticker, interval="minute1")
        self.ma15.extend(df["close"])
        self.ma50.extend(df["close"])
        self.ma120.extend(df["close"])

        self.price_curr = None
        self.hold_flag = False
        self.wait_flag = False

        self.cash = CASH

    def update(self, price_open, price_curr):
        # 기존에 저장된 값이 없다면, 입력된 값을 반영하겠다.
        if price_curr != None:
            self.ma15.append(price_curr)
            self.ma50.append(price_curr)
            self.ma120.append(price_curr)

        # 이동평균선 계산
        self.curr_ma15 = sum(self.ma15) / len(self.ma15)
        self.curr_ma50 = sum(self.ma50) / len(self.ma50)
        self.curr_ma120 = sum(self.ma120) / len(self.ma120)

        # 시가를 기반으로 매수, 매도가격을 설정
        if self.hold_flag == False:
            self.price_buy = price_open * 1.01
            self.price_sell = price_open * 1.02
        self.wait_flag = False

    def can_i_buy(self, price):
        return (
            self.hold_flag == False
            and self.wait_flag == False
            and price >= self.price_buy
            and self.curr_ma15 >= self.curr_ma50
            and self.curr_ma15 <= self.curr_ma50 * 1.03
            and self.curr_ma120 <= self.curr_ma50
        )

    def can_i_sell(self):
        return self.hold_flag == True

    def make_order(self):
        ret = self.buy_market_order(self.ticker, self.cash * 0.9995)
        print("매수주문", ret)

        order = self.get_order(ret["uuid"])
        print(order)
        volume = self.get_balance(self.ticker)

        ret = self.sell_limit_order(self.ticker, self.price_sell, volume)
        print("매도주문", ret)
        self.hold_flag = True

    def take_order(self):
        # 미체결 주문 리스트 조회
        uncomp = self.get_order(self.ticker)
        print(uncomp)
        self.cash = self.get_balance()
        self.cash = CASH
        print("매도완료", self.cash)
        self.hold_flag = False
        self.wait_flag = True


if __name__ == "__main__":
    with open("upbit.txt", "r") as f:
        key0 = f.readline().strip()
        key1 = f.readline().strip()

    upbit = RealCoin(key0, key1)
    # price = upbit.get_current_price("KRW-BTC")
    # print(price)
