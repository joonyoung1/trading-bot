import pandas as pd
import numpy as np


def calc_ratio(price: float, pivot_price: float):
    if price >= pivot_price:
        delta = (price / pivot_price) - 1
        ratio = -0.5 * (2**-delta) + 1
    else:
        delta = (pivot_price / price) - 1
        ratio = 0.5 * (2**-delta)
    return np.clip(ratio, 0.125, 0.875)


data = pd.read_csv("xrp_24h.csv")

initial_price = data.iloc[0]["o"]
initial_balance = 3000000
t = 0.005


for t in [0.003, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2]:
# for t in range(1, 10):
    # t /= 100
    # pivot_price = initial_price
    pivot_price = 1609
    last_trade_price = initial_price
    last_price = initial_price
    cash = initial_balance / 2
    quantity = (initial_balance / 2) / initial_price

    trade_count = 0

    for _, row in data.iterrows():
        if last_price <= row["t"]:
            prices = [row["o"], row["h"], row["l"], row["t"]]
        else:
            prices = [row["o"], row["l"], row["h"], row["t"]]
        last_price = prices[-1]

        for price in prices:
            while True:
                if last_trade_price * (1 + t) <= price:
                    trading_price = last_trade_price * (1 + t)
                elif last_trade_price * (1 - t) >= price:
                    trading_price = last_trade_price * (1 - t)
                else:
                    break

                if pivot_price >= trading_price * 3:
                    pivot_price = trading_price * 3
                elif pivot_price < trading_price / 3:
                    pivot_price = trading_price / 3

                ratio = calc_ratio(trading_price, pivot_price)
                
                volume = cash - (cash + quantity * trading_price) * ratio

                cash -= volume
                quantity += volume / trading_price
                cash -= volume * 0.0005

                last_trade_price = trading_price
                trade_count += 1

    # print(f"price: {price_series[-1]}")
    print(f"t: {t}")
    print(f"balance: {cash + quantity * data.iloc[-1]["t"]}")
    print(f"trade_count: {trade_count}")
