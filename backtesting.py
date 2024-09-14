import pyupbit
import matplotlib.pyplot as plt
import pandas as pd
from math import sqrt


if __name__ == "__main__":
    # df = pyupbit.get_ohlcv("KRW-XRP", interval="minute1", count=10000)
    df = pd.read_csv("xrp_30_100000.csv")
    prices = df["close"]
    initial_price = prices.iloc[0]

    market = []
    earn = []
    ratios = []

    initial_cash = 1000000
    cash = initial_cash
    quantity = 0
    trade_count = 0

    for price in prices:
        delta = price / initial_price - 1
        if delta == 0:
            ratio = 0.5
        elif delta < 0:
            # ratio = 0.5 - 0.5 * sqrt(abs(delta))
            ratio = 0.5 * delta**2 + delta + 0.5
            # ratio = 0.5 * delta + 0.5
        else:
            # ratio = 0.5 + 0.5 * sqrt(delta)
            ratio = (-2 ** -delta + 2) / 2
        

        value = price * quantity
        total_value = cash + value
        volume = cash - total_value * ratio

        if abs(volume) >= max(5001, total_value * 0.005):
            trade_count += 1
            cash -= volume
            cash -= abs(volume) * 0.0005
            quantity += volume / price

        earn.append(total_value / initial_cash - 1)
        market.append(price / initial_price - 1)
        ratios.append(ratio)


    print(f"{market[-1]:.2f}%, {earn[-1]:.2f}%")
    print(trade_count)

    plt.figure(figsize=(10, 6))
    plt.plot(market, label='Market Delta (%)', color='red', linestyle='-', linewidth=1.5)
    plt.plot(earn, label='Capital Delta (%)', color='orange', linestyle='--', linewidth=1.5)
    plt.plot(ratios, label='Ratio (%)', color='skyblue', linestyle='-.', linewidth=1.5)

    plt.title("Prices and Total Asset Value Over Time")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    plt.show()
