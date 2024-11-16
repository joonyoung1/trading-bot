def get_price_step(current_price: float) -> float:
    if current_price >= 2_000_000:
        return 1_000
    elif current_price >= 1_000_000:
        return 500
    elif current_price >= 500_000:
        return 100
    elif current_price >= 100_000:
        return 50
    elif current_price >= 10_000:
        return 10
    elif current_price >= 1_000:
        return 1
    elif current_price >= 100:
        return 0.1
    elif current_price >= 10:
        return 0.01
    elif current_price >= 1:
        return 0.001
    elif current_price >= 0.1:
        return 0.0001
    elif current_price >= 0.01:
        return 0.00001
    elif current_price >= 0.001:
        return 0.000001
    elif current_price >= 0.0001:
        return 0.0000001
    else:
        return 0.00000001


def get_upper_price(price: float) -> float:
    step = get_price_step(price)
    return price + step


def get_lower_price(price: float) -> float:
    step = get_price_step(price - 1e-6)
    return price - step
