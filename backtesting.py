import pyupbit
import matplotlib.pyplot as plt
import pandas as pd


if __name__ == "__main__":
    df = pyupbit.get_ohlcv("KRW-XRP", interval="minute1", count=10000)
    # df = pd.read_csv("xrp_30.csv")
    prices = df["close"]
    initial_price = prices.iloc[0]

    market = []
    earn = []

    initial_cash = 500000
    cash = initial_cash
    quantity = 0
    trade_count = 0

    for price in prices:
        asset_value = price * quantity
        trade_volume = (cash - asset_value) / 2
        volume = abs(trade_volume)

        ratio = asset_value / (asset_value + cash)
        if volume < 5001 or 0.5 <= ratio <= 0.505:
            earn.append(((cash + price * quantity) / initial_cash - 1) * 100)
            market.append((price / initial_price - 1) * 100)
            continue
        
        trade_count += 1
        cash -= trade_volume
        cash -= volume * 0.005
        quantity += trade_volume / price

        earn.append(((cash + price * quantity) / initial_cash - 1) * 100)
        market.append((price / initial_price - 1) * 100)


    print(f"{market[-1]:.2f}%, {earn[-1]:.2f}%")
    print(trade_count)

    plt.figure(figsize=(10, 6))
    plt.plot(market, label="Prices", color="blue")
    plt.plot(earn, label="Value", color="green")

    plt.title("Prices and Total Asset Value Over Time")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    plt.show()
