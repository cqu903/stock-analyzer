"""
技术指标计算模块
提供MACD、RSI、KDJ、MA等常用技术指标的计算函数
"""

from decimal import Decimal

import pandas as pd

from src.models.schemas import KDJResult, MACDResult


def calc_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult:
    """计算MACD指标

    Args:
        df: 包含行情数据的DataFrame，必须有close列
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9

    Returns:
        MACDResult: 包含DIF、DEA、MACD柱值的结果
    """
    closes = df["close"]
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = (dif - dea) * 2

    return MACDResult(
        dif=Decimal(str(dif.iloc[-1])),
        dea=Decimal(str(dea.iloc[-1])),
        macd=Decimal(str(macd.iloc[-1])),
    )


def calc_rsi(df: pd.DataFrame, period: int = 14) -> Decimal:
    """计算RSI指标

    Args:
        df: 包含行情数据的DataFrame，必须有close列
        period: RSI周期，默认14

    Returns:
        Decimal: RSI值（0-100）
    """
    closes = df["close"]
    delta = closes.diff()

    gain = delta.where(delta > 0, 0)
    loss = (-delta.where(delta < 0, 0)).abs()

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return Decimal(str(rsi.iloc[-1]))


def calc_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> KDJResult:
    """计算KDJ指标

    Args:
        df: 包含行情数据的DataFrame，必须有high、low、close列
        n: RSV周期，默认9
        m1: K值平滑周期，默认3
        m2: D值平滑周期，默认3

    Returns:
        KDJResult: 包含K、D、J值的结果
    """
    low_min = df["low"].rolling(window=n, min_periods=n).min()
    high_max = df["high"].rolling(window=n, min_periods=n).max()

    rsv = (df["close"] - low_min) / (high_max - low_min) * 100
    rsv = rsv.fillna(50)

    k = rsv.ewm(span=m1, adjust=False).mean()
    d = k.ewm(span=m2, adjust=False).mean()
    j = 3 * k - 2 * d

    return KDJResult(
        k=Decimal(str(k.iloc[-1])),
        d=Decimal(str(d.iloc[-1])),
        j=Decimal(str(j.iloc[-1])),
    )


def calc_ma(df: pd.DataFrame, periods: list[int] = None) -> dict[int, Decimal]:
    """计算均线

    Args:
        df: 包含行情数据的DataFrame，必须有close列
        periods: 均线周期列表，默认[5, 10, 20, 60]

    Returns:
        dict[int, Decimal]: 周期到均线值的映射
    """
    if periods is None:
        periods = [5, 10, 20, 60]

    result = {}
    for period in periods:
        if len(df) >= period:
            ma = df["close"].rolling(window=period).mean().iloc[-1]
            result[period] = Decimal(str(ma))
    return result


def calc_bollinger_bands(
    df: pd.DataFrame, period: int = 20, std_dev: float = 2.0
) -> dict[str, Decimal]:
    """计算布林带

    Args:
        df: 包含行情数据的DataFrame，必须有close列
        period: 周期，默认20
        std_dev: 标准差倍数，默认2.0

    Returns:
        dict[str, Decimal]: 包含upper、middle、lower的字典
    """
    closes = df["close"]
    middle = closes.rolling(window=period).mean()
    std = closes.rolling(window=period).std()
    upper = middle + std * std_dev
    lower = middle - std * std_dev

    return {
        "upper": Decimal(str(upper.iloc[-1])),
        "middle": Decimal(str(middle.iloc[-1])),
        "lower": Decimal(str(lower.iloc[-1])),
    }


def calc_atr(df: pd.DataFrame, period: int = 14) -> Decimal:
    """计算ATR（平均真实波幅）

    Args:
        df: 包含行情数据的DataFrame，必须有high、low、close列
        period: 周期，默认14

    Returns:
        Decimal: ATR值
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()

    return Decimal(str(atr.iloc[-1]))
