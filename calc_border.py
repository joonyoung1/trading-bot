import sys


def calc_volume(initial_price, quantity, cash, current_price):
    delta = current_price / initial_price - 1
    if delta == 0:
        ratio = 0.5
    elif delta < 0:
        ratio = 0.5 * delta**2 + delta + 0.5
    else:
        ratio = -0.5 * 2**-delta + 1

    total_value = quantity * current_price + cash
    proper_cash = total_value * ratio
    return cash - proper_cash


def calc_border(initial_price, pivot, quantity, cash):
    lower_price = pivot
    while True:
        lower_price = ((lower_price * 10) - 1) / 10
        volume = calc_volume(initial_price, quantity, cash, lower_price)
        if abs(volume) > 5000:
            break

    upper_price = pivot
    while True:
        upper_price = ((upper_price * 10) + 1) / 10
        volume = calc_volume(initial_price, quantity, cash, upper_price)
        if abs(volume) > 5000:
            break

    return lower_price, upper_price


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script_name.py <initial_price> <pivot> <quantity> <cash>")
        sys.exit(1)

    initial_price = float(sys.argv[1])
    pivot = float(sys.argv[2])
    quantity = float(sys.argv[3])
    cash = float(sys.argv[4])

    print(calc_volume(initial_price, quantity, cash, pivot))
    print(calc_border(initial_price, pivot, quantity, cash))
