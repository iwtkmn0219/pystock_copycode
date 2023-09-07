import threading
import queue
import time
import pyupbit
from collections import deque
import datetime
import realcoin

with open("coin_list.txt", "r") as f:
    tickers = f.readline().split()


class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

        with open("upbit.txt", "r") as f:
            key0 = f.readline().strip()
            key1 = f.readline().strip()

        self.u = {}
        for ticker in tickers:
            self.u[ticker] = realcoin.Real1Percent(key0, key1, ticker)

    # 큐에서 데이터를 가져와서 출력
    def run(self):
        # 현재가 정보
        price_curr = {}
        for ticker in tickers:
            price_curr[ticker] = None

        i = 0
        while True:
            try:
                # 큐에 데이터가 있는 경우만 Get
                if not self.q.empty():
                    price_open = self.q.get()

                    for ticker in price_open:
                        self.u[ticker].update(price_open[ticker], price_curr[ticker])
                    print("Update Finished")

                price_curr = pyupbit.get_current_price(tickers)

                for ticker in tickers:
                    if self.u[ticker].can_i_buy(price_curr[ticker]):
                        self.u[ticker].make_order()

                    if self.u[ticker].can_i_sell():
                        self.u[ticker].take_order()

                # 1분
                if i == (5 * 60 * 3):
                    now = datetime.datetime.now()
                    for ticker in tickers:
                        print(
                            f"[{now}] {ticker} : 현재가 {price_curr[ticker]}, 목표가 {self.u[ticker].price_buy}, ma {self.u[ticker].curr_ma15:.2f}/{self.u[ticker].curr_ma50:.2f}/{self.u[ticker].curr_ma120:.2f}, hold_flag {self.u[ticker].hold_flag}, wait_flag {self.u[ticker].wait_flag}"
                        )
                    i = 0
                i += 1
            except:
                print("error")

            time.sleep(0.2)


class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q

    # 현재 시가를 조회하여 큐에 삽입
    def run(self):
        while True:
            prices = pyupbit.get_current_price(tickers)
            self.q.put(prices)
            time.sleep(60)


q = queue.Queue()
Producer(q).start()
Consumer(q).start()
