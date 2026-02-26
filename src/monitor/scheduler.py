"""
定时任务调度器
使用APScheduler实现定时任务调度，包括：
- 每15分钟更新自选股行情
- 每日16:00同步日线数据
- 每15分钟检查预警条件
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from config.settings import Settings
from src.data.repository import Repository


class DataScheduler:
    """数据定时任务调度器

    负责调度以下定时任务：
    1. update_watchlist_quotes: 每15分钟更新自选股行情
    2. sync_daily_data: 每日16:00同步日线数据
    3. check_alerts: 每15分钟检查预警条件
    """

    def __init__(self, settings: Settings, repository: Repository):
        """初始化调度器

        Args:
            settings: 应用配置
            repository: 数据访问层
        """
        self.settings = settings
        self.repository = repository
        self._scheduler: BackgroundScheduler | None = None
        logger.info("DataScheduler initialized")

    def _update_watchlist_quotes(self):
        """更新自选股行情

        从数据源获取最新行情数据并保存到数据库
        """
        try:
            watchlist = self.repository.get_watchlist()
            if not watchlist:
                logger.debug("No watchlist items to update")
                return

            logger.info(f"Updating quotes for {len(watchlist)} watchlist items")
            # TODO: 实现从数据源获取最新行情的逻辑
            # 这需要访问数据源provider，可以通过注入或工厂模式获取
            logger.debug("Watchlist quotes updated")
        except Exception as e:
            logger.error(f"Error updating watchlist quotes: {e}")

    def _sync_daily_data(self):
        """同步日线数据

        每日收盘后同步所有自选股的日线数据
        """
        try:
            watchlist = self.repository.get_watchlist()
            if not watchlist:
                logger.debug("No watchlist items to sync")
                return

            logger.info(f"Syncing daily data for {len(watchlist)} watchlist items")
            # TODO: 实现从数据源同步日线数据的逻辑
            logger.debug("Daily data synced")
        except Exception as e:
            logger.error(f"Error syncing daily data: {e}")

    def _check_alerts(self):
        """检查预警条件

        检查所有自选股的预警条件是否触发
        """
        try:
            from src.monitor.alerts import AlertEngine

            engine = AlertEngine(self.repository)
            alerts = engine.check_all()

            if alerts:
                logger.info(f"Generated {len(alerts)} alerts")
            else:
                logger.debug("No alerts triggered")
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def start(self):
        """启动调度器

        添加并启动以下定时任务：
        - update_watchlist_quotes: 每15分钟执行一次
        - sync_daily_data: 每日16:00执行
        - check_alerts: 每15分钟执行一次
        """
        if self._scheduler is not None and self._scheduler.running:
            logger.warning("Scheduler is already running")
            return

        self._scheduler = BackgroundScheduler()

        # 每15分钟更新自选股行情
        self._scheduler.add_job(
            self._update_watchlist_quotes,
            "interval",
            minutes=15,
            id="update_watchlist_quotes",
            replace_existing=True,
        )

        # 每日16:00同步日线数据
        self._scheduler.add_job(
            self._sync_daily_data,
            "cron",
            hour=16,
            minute=0,
            id="sync_daily_data",
            replace_existing=True,
        )

        # 每15分钟检查预警条件
        self._scheduler.add_job(
            self._check_alerts,
            "interval",
            minutes=15,
            id="check_alerts",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("DataScheduler started with jobs: update_watchlist_quotes, sync_daily_data, check_alerts")

    def stop(self):
        """停止调度器

        优雅地关闭调度器，等待所有正在执行的任务完成
        """
        if self._scheduler is None:
            logger.warning("Scheduler is not running")
            return

        if not self._scheduler.running:
            logger.info("Scheduler is already stopped")
            return

        self._scheduler.shutdown(wait=True)
        logger.info("DataScheduler stopped")
