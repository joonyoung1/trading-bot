import pyupbit
import matplotlib.pyplot as plt
import sys


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python backtesting.py <interval> <count>")
        sys.exit(1)

    interval = sys.argv[1]
    count = int(sys.argv[2])

    df = pyupbit.get_ohlcv("KRW-XRP", interval=interval, count=count)
    prices = df["close"]
    initial_price = prices.iloc[0]

    market = []
    earn = []
    ratios = []

    initial_cash = 1000000
    cash = initial_cash / 2
    quantity = cash / initial_price
    last_trade_price = initial_price
    trade_count = 0

    for price in prices:
        if abs(price / last_trade_price - 1) <= 0.002:
            continue

        delta = price / initial_price - 1
        if delta == 0:
            ratio = 0.5
        elif delta < 0:
            ratio = 0.5 * delta**2 + delta + 0.5
        else:
            ratio = -0.5 * 2**-delta + 1

        value = price * quantity
        total_value = cash + value
        volume = cash - total_value * ratio

        if abs(volume) >= max(5001, total_value * 0.005):
            trade_count += 1
            last_trade_price = price
            cash -= volume
            cash -= abs(volume) * 0.0005
            quantity += volume / price

        earn.append(total_value / initial_cash - 1)
        market.append(price / initial_price - 1)
        ratios.append(ratio)

    print(f"market delta : {market[-1] * 100:.2f}%")
    print(f"earn delta : {earn[-1] * 100:.2f}%")
    print(f"trade count : {trade_count}")

    plt.figure(figsize=(10, 6))
    plt.plot(
        market, label="Market Delta (%)", color="red", linestyle="-", linewidth=1.5
    )
    plt.plot(
        earn, label="Capital Delta (%)", color="orange", linestyle="--", linewidth=1.5
    )
    plt.plot(ratios, label="Ratio (%)", color="skyblue", linestyle="-.", linewidth=1.5)

    plt.title("Prices and Total Asset Value Over Time")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()

    plt.show()
