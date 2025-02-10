import asyncio

from bayes_opt import BayesianOptimization

from fetch_candle import fetch_price_series
from app.utils import calc_ratio


def simulate(t: float, price_series):
    initial_price = price_series[0]
    initial_balance = 10000000
    pivot_price = initial_price
    last_trade_price = initial_price

    cash = initial_balance / 2
    quantity = (initial_balance / 2) / initial_price
    trade_count = 0

    for price in price_series:
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

    return cash + quantity * price_series[-1]


async def main():
    price_series = await fetch_price_series()

    def objective_function(t):
        # t = np.exp(log_t)
        return simulate(t, price_series)

    optimizer = BayesianOptimization(
        f=objective_function,
        pbounds={"t": (0.003, 0.05)},
        random_state=42,
        verbose=2,
    )

    optimizer.maximize(init_points=5, n_iter=25)

    print(f"best_t: {optimizer.max["params"]["t"]}")
    print(f"best_balance: {optimizer.max["target"]}")


if __name__ == "__main__":
    asyncio.run(main())
