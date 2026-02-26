"""
预警引擎
负责检查自选股的预警条件，包括：
- 价格上限/下限预警
- 异常波动预警（涨跌幅>=5%）
- MACD金叉预警
- RSI超买/超卖预警
"""

from datetime import datetime

import pandas as pd
from loguru import logger

from src.analysis.indicators import calc_macd, calc_rsi
from src.data.repository import Repository
from src.models.schemas import Alert, AlertType, WatchlistItem


class AlertEngine:
    """预警引擎

    负责检查所有自选股的预警条件，并在触发时保存预警记录
    """

    # 异常波动阈值（百分比）
    VOLATILITY_THRESHOLD = 5.0

    # RSI超买/超卖阈值
    RSI_OVERBOUGHT_THRESHOLD = 80
    RSI_OVERSOLD_THRESHOLD = 20

    def __init__(self, repository: Repository):
        """初始化预警引擎

        Args:
            repository: 数据访问层
        """
        self.repository = repository
        logger.info("AlertEngine initialized")

    def check_all(self) -> list[Alert]:
        """检查所有自选股的预警条件

        Returns:
            触发的预警列表
        """
        watchlist = self.repository.get_watchlist()
        if not watchlist:
            logger.debug("No watchlist items to check")
            return []

        all_alerts: list[Alert] = []

        for item in watchlist:
            try:
                alerts = self._check_item(item)
                all_alerts.extend(alerts)
            except Exception as e:
                logger.error(f"Error checking alerts for {item.symbol}: {e}")

        # 保存所有预警到数据库
        for alert in all_alerts:
            self.repository.save_alert(alert)

        return all_alerts

    def _check_item(self, item: WatchlistItem) -> list[Alert]:
        """检查单个自选股的预警条件

        Args:
            item: 自选股项目

        Returns:
            触发的预警列表
        """
        alerts: list[Alert] = []
        symbol = item.symbol

        # 获取历史行情数据（至少需要60天用于计算技术指标）
        quotes = self.repository.get_quotes(symbol, days=90)
        if len(quotes) < 2:
            logger.debug(f"Not enough quotes for {symbol}, skipping alert check")
            return alerts

        # 转换为DataFrame便于计算
        df = self._quotes_to_dataframe(quotes)

        # 获取最新行情
        latest_quote = quotes[-1]

        # 1. 检查价格上限/下限预警
        alerts.extend(self._check_price_alerts(symbol, item, latest_quote))

        # 2. 检查异常波动预警
        alerts.extend(self._check_volatility_alert(symbol, latest_quote))

        # 3. 检查MACD金叉预警
        alerts.extend(self._check_macd_golden_cross(symbol, df))

        # 4. 检查RSI超买/超卖预警
        alerts.extend(self._check_rsi_alerts(symbol, df))

        return alerts

    def _check_price_alerts(
        self, symbol: str, item: WatchlistItem, latest_quote
    ) -> list[Alert]:
        """检查价格上限/下限预警

        Args:
            symbol: 股票代码
            item: 自选股项目（包含预警价格设置）
            latest_quote: 最新行情

        Returns:
            触发的预警列表
        """
        alerts: list[Alert] = []
        current_price = float(latest_quote.close)

        # 检查价格上限
        if item.alert_price_high is not None:
            high_threshold = float(item.alert_price_high)
            if current_price >= high_threshold:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.PRICE_BREAK,
                    message=f"价格突破上限: 当前价格 {current_price:.2f} >= 上限 {high_threshold:.2f}",
                    triggered_at=datetime.now(),
                    is_read=False,
                )
                alerts.append(alert)
                logger.info(f"Price high alert triggered for {symbol}: {current_price:.2f} >= {high_threshold:.2f}")

        # 检查价格下限
        if item.alert_price_low is not None:
            low_threshold = float(item.alert_price_low)
            if current_price <= low_threshold:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.PRICE_BREAK,
                    message=f"价格突破下限: 当前价格 {current_price:.2f} <= 下限 {low_threshold:.2f}",
                    triggered_at=datetime.now(),
                    is_read=False,
                )
                alerts.append(alert)
                logger.info(f"Price low alert triggered for {symbol}: {current_price:.2f} <= {low_threshold:.2f}")

        return alerts

    def _check_volatility_alert(self, symbol: str, latest_quote) -> list[Alert]:
        """检查异常波动预警

        Args:
            symbol: 股票代码
            latest_quote: 最新行情

        Returns:
            触发的预警列表
        """
        alerts: list[Alert] = []

        if latest_quote.change_pct is None:
            return alerts

        change_pct = float(latest_quote.change_pct)

        # 检查涨跌幅是否超过阈值
        if abs(change_pct) >= self.VOLATILITY_THRESHOLD:
            direction = "上涨" if change_pct > 0 else "下跌"
            alert = Alert(
                symbol=symbol,
                alert_type=AlertType.ABNORMAL_VOLATILITY,
                message=f"异常波动: {direction} {abs(change_pct):.2f}%",
                triggered_at=datetime.now(),
                is_read=False,
            )
            alerts.append(alert)
            logger.info(f"Volatility alert triggered for {symbol}: {direction} {abs(change_pct):.2f}%")

        return alerts

    def _check_macd_golden_cross(self, symbol: str, df: pd.DataFrame) -> list[Alert]:
        """检查MACD金叉预警

        Args:
            symbol: 股票代码
            df: 包含历史行情的DataFrame

        Returns:
            触发的预警列表
        """
        alerts: list[Alert] = []

        # 至少需要26个数据点才能计算MACD
        if len(df) < 26:
            return alerts

        try:
            # 计算当前MACD
            current_macd = calc_macd(df)

            # 计算前一天的MACD用于判断是否刚发生金叉
            prev_df = df.iloc[:-1]
            if len(prev_df) >= 26:
                prev_macd = calc_macd(prev_df)

                # 判断金叉：当前DIF>DEA且MACD>0，且前一天不满足
                is_golden_cross = (
                    current_macd.is_golden_cross()
                    and not prev_macd.is_golden_cross()
                )

                if is_golden_cross:
                    alert = Alert(
                        symbol=symbol,
                        alert_type=AlertType.MACD_GOLDEN_CROSS,
                        message=f"MACD金叉: DIF({current_macd.dif:.4f}) > DEA({current_macd.dea:.4f})",
                        triggered_at=datetime.now(),
                        is_read=False,
                    )
                    alerts.append(alert)
                    logger.info(f"MACD golden cross alert triggered for {symbol}")

        except Exception as e:
            logger.debug(f"Error checking MACD for {symbol}: {e}")

        return alerts

    def _check_rsi_alerts(self, symbol: str, df: pd.DataFrame) -> list[Alert]:
        """检查RSI超买/超卖预警

        Args:
            symbol: 股票代码
            df: 包含历史行情的DataFrame

        Returns:
            触发的预警列表
        """
        alerts: list[Alert] = []

        # 至少需要14个数据点才能计算RSI
        if len(df) < 14:
            return alerts

        try:
            rsi = calc_rsi(df)
            rsi_value = float(rsi)

            # 检查RSI超买
            if rsi_value > self.RSI_OVERBOUGHT_THRESHOLD:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.RSI_OVERBOUGHT,
                    message=f"RSI超买: RSI({rsi_value:.2f}) > {self.RSI_OVERBOUGHT_THRESHOLD}",
                    triggered_at=datetime.now(),
                    is_read=False,
                )
                alerts.append(alert)
                logger.info(f"RSI overbought alert triggered for {symbol}: {rsi_value:.2f}")

            # 检查RSI超卖
            elif rsi_value < self.RSI_OVERSOLD_THRESHOLD:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.RSI_OVERSOLD,
                    message=f"RSI超卖: RSI({rsi_value:.2f}) < {self.RSI_OVERSOLD_THRESHOLD}",
                    triggered_at=datetime.now(),
                    is_read=False,
                )
                alerts.append(alert)
                logger.info(f"RSI oversold alert triggered for {symbol}: {rsi_value:.2f}")

        except Exception as e:
            logger.debug(f"Error checking RSI for {symbol}: {e}")

        return alerts

    def _quotes_to_dataframe(self, quotes: list) -> pd.DataFrame:
        """将行情列表转换为DataFrame

        Args:
            quotes: 行情列表

        Returns:
            包含行情数据的DataFrame
        """
        data = {
            "open": [float(q.open) for q in quotes],
            "high": [float(q.high) for q in quotes],
            "low": [float(q.low) for q in quotes],
            "close": [float(q.close) for q in quotes],
            "volume": [q.volume for q in quotes],
        }
        return pd.DataFrame(data)
