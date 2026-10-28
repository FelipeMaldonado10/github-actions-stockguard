FACTOR_SOBRESTOCK = 3


def _validar_stock(stock_actual: int, stock_minimo: int) -> None:
    if stock_actual < 0:
        raise ValueError("El stock actual no puede ser negativo")
    if stock_minimo <= 0:
        raise ValueError("El stock minimo debe ser mayor que cero")


def clasificar_stock(stock_actual: int, stock_minimo: int) -> str:
    _validar_stock(stock_actual, stock_minimo)

    if stock_actual == 0:
        return "AGOTADO"
    if stock_actual <= stock_minimo * 0.5:
        return "CRITICO"
    if stock_actual <= stock_minimo:
        return "BAJO"
    return "NORMAL"


def detectar_sobrestock(stock_actual: int, stock_minimo: int) -> bool:
    """Indica si el stock supera tres veces el minimo requerido."""
    _validar_stock(stock_actual, stock_minimo)
    return stock_actual > stock_minimo * FACTOR_SOBRESTOCK
