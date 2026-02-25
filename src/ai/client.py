"""
AI客户端
封装OpenAI API调用，提供股票分析和对话功能
"""

from datetime import datetime
from typing import Optional

from openai import OpenAI
from loguru import logger

from src.models.schemas import AIAnalysis


class AIClient:
    """AI客户端类

    封装OpenAI API调用，提供股票分析和智能对话功能
    """

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4"):
        """初始化AI客户端

        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL
            model: 模型名称，默认gpt-4
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        logger.info(f"AIClient initialized with model={model}")

    def analyze_stock(self, symbol: str, fundamental: dict, technical: dict) -> AIAnalysis:
        """综合分析股票

        Args:
            symbol: 股票代码
            fundamental: 基本面数据字典
            technical: 技术面数据字典

        Returns:
            AIAnalysis: AI分析结果
        """
        from src.ai.prompts import Prompts

        prompt = Prompts.stock_analysis(symbol, fundamental, technical)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": Prompts.SYSTEM_ANALYST},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content or "分析完成但无返回内容"
            return AIAnalysis(
                symbol=symbol,
                summary=content,
                generated_at=datetime.now(),
                confidence=80,  # 默认置信度
            )
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return AIAnalysis(
                symbol=symbol,
                summary=f"分析失败: {str(e)}",
                generated_at=datetime.now(),
                confidence=0,
            )

    def chat(self, messages: list[dict], user_message: str) -> str:
        """对话式问答

        Args:
            messages: 历史消息列表
            user_message: 用户消息

        Returns:
            str: AI回复内容
        """
        all_messages = messages + [{"role": "user", "content": user_message}]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                temperature=0.7,
            )
            return response.choices[0].message.content or "抱歉，我无法生成回复。"
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            return f"抱歉，我遇到了一些问题: {str(e)}"

    def quick_analyze(self, symbol: str, question: str) -> str:
        """快速分析股票

        Args:
            symbol: 股票代码
            question: 用户问题

        Returns:
            str: AI回复
        """
        from src.ai.prompts import Prompts

        context = f"股票代码: {symbol}"
        prompt = Prompts.quick_question(question, context)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": Prompts.SYSTEM_ANALYST},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content or "无法生成分析"
        except Exception as e:
            logger.error(f"快速分析失败: {e}")
            return f"分析失败: {str(e)}"
