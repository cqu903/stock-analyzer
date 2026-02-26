"""
技术面分析器
提供趋势分析、支撑压力位识别、K线形态检测等功能
"""

from datetime import date
from decimal import Decimal

import pandas as pd
from loguru import logger

from src.analysis.indicators import calc_kdj, calc_ma, calc_macd, calc_rsi
from src.data.repository import Repository
from src.models.schemas import (
    DailyQuote,
    Indicators,
    SupportResistance,
    TechnicalReport,
    TrendResult,
)


class TechnicalAnalyzer:
    """技术面分析器

    对股票进行技术分析，包括趋势判断、指标计算、支撑压力位识别、K线形态检测等
    """

    def __init__(self, repository: Repository):
        """初始化技术分析器

        Args:
            repository: 数据访问层实例
        """
        self.repository = repository
        logger.info("TechnicalAnalyzer initialized")

    def analyze(self, symbol: str, days: int = 365) -> TechnicalReport:
        """执行技术面分析

        Args:
            symbol: 股票代码
            days: 分析天数，默认365天

        Returns:
            TechnicalReport: 技术面分析报告
        """
        logger.info(f"Starting technical analysis for {symbol}, days={days}")

        # 获取行情数据
        quotes = self.repository.get_quotes(symbol, days)
        if not quotes or len(quotes) < 20:
            logger.warning(f"Insufficient data for {symbol}: {len(quotes) if quotes else 0} quotes")
            return TechnicalReport(
                symbol=symbol,
                analysis_date=date.today(),
                score=0,
                summary="数据不足，无法进行技术分析",
            )

        # 转换为DataFrame
        df = self._quotes_to_dataframe(quotes)

        # 分析趋势
        trend = self._analyze_trend(df)

        # 计算技术指标
        indicators = self._calculate_indicators(df)

        # 识别支撑压力位
        support_resistance = self._find_support_resistance(df)

        # 检测K线形态
        patterns = self._detect_patterns(df)

        # 计算综合评分
        score = self._calculate_score(trend, indicators, patterns)

        report = TechnicalReport(
            symbol=symbol,
            analysis_date=date.today(),
            trend=trend,
            indicators=indicators,
            support_resistance=support_resistance,
            patterns=patterns,
            score=score,
        )

        logger.info(f"Technical analysis completed for {symbol}, score={score}")
        return report

    def _quotes_to_dataframe(self, quotes: list[DailyQuote]) -> pd.DataFrame:
        """将行情列表转换为DataFrame

        Args:
            quotes: 行情数据列表

        Returns:
            pd.DataFrame: 转换后的DataFrame
        """
        data = {
            "trade_date": [q.trade_date for q in quotes],
            "open": [float(q.open) for q in quotes],
            "high": [float(q.high) for q in quotes],
            "low": [float(q.low) for q in quotes],
            "close": [float(q.close) for q in quotes],
            "volume": [q.volume for q in quotes],
        }
        df = pd.DataFrame(data)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.sort_values("trade_date").reset_index(drop=True)
        return df

    def _analyze_trend(self, df: pd.DataFrame) -> TrendResult:
        """分析趋势方向

        Args:
            df: 行情数据DataFrame

        Returns:
            TrendResult: 趋势分析结果
        """
        closes = df["close"]
        current_price = Decimal(str(closes.iloc[-1]))

        # 计算不同周期的均线
        ma5 = closes.rolling(window=5).mean().iloc[-1]
        ma10 = closes.rolling(window=10).mean().iloc[-1]
        ma20 = closes.rolling(window=20).mean().iloc[-1]

        # 计算短期趋势（5日vs10日）
        short_trend = "上涨" if ma5 > ma10 else "下跌"

        # 计算中期趋势（10日vs20日）
        mid_trend = "上涨" if ma10 > ma20 else "下跌"

        # 计算趋势强度（基于最近N日的涨跌幅）
        recent_returns = closes.pct_change().tail(20)
        positive_days = (recent_returns > 0).sum()
        trend_strength = positive_days / len(recent_returns)

        # 判断趋势方向
        if trend_strength > 0.65 and short_trend == "上涨" and mid_trend == "上涨":
            direction = "强势上涨"
        elif trend_strength > 0.55 and short_trend == "上涨":
            direction = "震荡偏强"
        elif trend_strength < 0.35 and short_trend == "下跌" and mid_trend == "下跌":
            direction = "弱势下跌"
        elif trend_strength < 0.45 and short_trend == "下跌":
            direction = "震荡偏弱"
        else:
            direction = "横盘整理"

        return TrendResult(
            direction=direction,
            current_price=current_price,
        )

    def _calculate_indicators(self, df: pd.DataFrame) -> Indicators:
        """计算技术指标

        Args:
            df: 行情数据DataFrame

        Returns:
            Indicators: 技术指标集合
        """
        # 计算MA
        ma_dict = calc_ma(df, [5, 10, 20, 60])

        # 计算MACD
        macd_result = calc_macd(df) if len(df) >= 26 else None

        # 计算KDJ
        kdj_result = calc_kdj(df) if len(df) >= 9 else None

        # 计算RSI
        rsi_result = calc_rsi(df) if len(df) >= 14 else None

        return Indicators(
            ma5=ma_dict.get(5),
            ma10=ma_dict.get(10),
            ma20=ma_dict.get(20),
            ma60=ma_dict.get(60),
            macd=macd_result,
            kdj=kdj_result,
            rsi=rsi_result,
        )

    def _find_support_resistance(self, df: pd.DataFrame) -> SupportResistance:
        """识别支撑压力位

        Args:
            df: 行情数据DataFrame

        Returns:
            SupportResistance: 支撑压力位
        """
        # 使用最近60日的数据
        lookback = min(60, len(df))
        recent_df = df.tail(lookback)

        highs = recent_df["high"]
        lows = recent_df["low"]
        closes = recent_df["close"]

        current_price = closes.iloc[-1]

        # 找出局部高点和低点
        resistance_levels = []
        support_levels = []

        # 简单方法：找出过去的高点和低点
        for i in range(2, len(recent_df) - 2):
            # 局部高点
            if (
                highs.iloc[i] > highs.iloc[i - 1]
                and highs.iloc[i] > highs.iloc[i - 2]
                and highs.iloc[i] > highs.iloc[i + 1]
                and highs.iloc[i] > highs.iloc[i + 2]
            ):
                if highs.iloc[i] > current_price:
                    resistance_levels.append(highs.iloc[i])

            # 局部低点
            if (
                lows.iloc[i] < lows.iloc[i - 1]
                and lows.iloc[i] < lows.iloc[i - 2]
                and lows.iloc[i] < lows.iloc[i + 1]
                and lows.iloc[i] < lows.iloc[i + 2]
            ):
                if lows.iloc[i] < current_price:
                    support_levels.append(lows.iloc[i])

        # 排序并取最近的支撑压力位
        resistance_levels = sorted(resistance_levels)
        support_levels = sorted(support_levels, reverse=True)

        # 第一压力位：最近的上方压力
        resistance_1 = Decimal(str(resistance_levels[0])) if resistance_levels else Decimal(str(current_price * 1.05))

        # 第二压力位：更远的上方压力
        resistance_2 = Decimal(str(resistance_levels[1])) if len(resistance_levels) > 1 else None

        # 第一支撑位：最近的下方支撑
        support_1 = Decimal(str(support_levels[0])) if support_levels else Decimal(str(current_price * 0.95))

        # 第二支撑位：更远的下方支撑
        support_2 = Decimal(str(support_levels[1])) if len(support_levels) > 1 else None

        return SupportResistance(
            resistance_1=resistance_1,
            resistance_2=resistance_2,
            support_1=support_1,
            support_2=support_2,
        )

    def _detect_patterns(self, df: pd.DataFrame) -> list[str]:
        """检测K线形态

        Args:
            df: 行情数据DataFrame

        Returns:
            list[str]: 检测到的K线形态列表
        """
        patterns = []

        if len(df) < 3:
            return patterns

        # 获取最近几根K线
        recent = df.tail(5)

        for i in range(len(recent) - 1, max(len(recent) - 4, 0), -1):
            open_price = recent["open"].iloc[i]
            high_price = recent["high"].iloc[i]
            low_price = recent["low"].iloc[i]
            close_price = recent["close"].iloc[i]

            # 计算实体和影线
            body = abs(close_price - open_price)
            total_range = high_price - low_price
            upper_shadow = high_price - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low_price

            if total_range == 0:
                continue

            # 大阳线：实体占比>70%，收盘接近最高
            if close_price > open_price and body / total_range > 0.7:
                patterns.append("大阳线")

            # 大阴线：实体占比>70%，收盘接近最低
            if close_price < open_price and body / total_range > 0.7:
                patterns.append("大阴线")

            # 十字星：实体很小，上下影线较长
            if body / total_range < 0.1 and upper_shadow > body and lower_shadow > body:
                patterns.append("十字星")

            # 锤子线：下影线长，实体小，上影线短
            if (
                lower_shadow > body * 2
                and upper_shadow < body * 0.5
                and close_price > open_price
            ):
                patterns.append("锤子线")

            # 倒锤线：上影线长，实体小，下影线短
            if (
                upper_shadow > body * 2
                and lower_shadow < body * 0.5
                and close_price > open_price
            ):
                patterns.append("倒锤线")

            # 流星线：上影线长，实体小，出现在上涨趋势中
            if (
                upper_shadow > body * 2
                and lower_shadow < body * 0.5
                and close_price < open_price
            ):
                patterns.append("流星线")

        # 去重
        patterns = list(dict.fromkeys(patterns))

        return patterns

    def _calculate_score(
        self,
        trend: TrendResult,
        indicators: Indicators,
        patterns: list[str],
    ) -> int:
        """计算技术面综合评分

        Args:
            trend: 趋势分析结果
            indicators: 技术指标
            patterns: K线形态

        Returns:
            int: 综合评分（0-100）
        """
        score = 50  # 基础分

        # 趋势评分
        trend_scores = {
            "强势上涨": 20,
            "震荡偏强": 10,
            "横盘整理": 0,
            "震荡偏弱": -10,
            "弱势下跌": -20,
        }
        score += trend_scores.get(trend.direction, 0)

        # MACD评分
        if indicators.macd:
            if indicators.macd.is_golden_cross():
                score += 10
            elif indicators.macd.macd < 0:
                score -= 5

        # RSI评分
        if indicators.rsi:
            if indicators.rsi < 30:
                score += 10  # 超卖，可能反弹
            elif indicators.rsi > 70:
                score -= 10  # 超买，可能回调

        # KDJ评分
        if indicators.kdj:
            if indicators.kdj.j < 20:
                score += 5  # 超卖
            elif indicators.kdj.j > 80:
                score -= 5  # 超买

        # K线形态评分
        bullish_patterns = ["大阳线", "锤子线", "倒锤线"]
        bearish_patterns = ["大阴线", "流星线"]

        for pattern in patterns:
            if pattern in bullish_patterns:
                score += 5
            elif pattern in bearish_patterns:
                score -= 5

        # 限制在0-100范围内
        return max(0, min(100, score))
