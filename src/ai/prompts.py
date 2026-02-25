"""
AI提示词模板
定义股票分析相关的提示词模板
"""


class Prompts:
    """提示词模板类"""

    SYSTEM_ANALYST = """你是一位专业的股票分析师，擅长基本面和技术面分析。
你的分析应该：
1. 客观中立，基于数据说话
2. 指出风险点和机会点
3. 给出明确的操作建议（买入/持有/卖出）及理由
4. 使用中文回复，语言简洁专业"""

    @staticmethod
    def stock_analysis(symbol: str, fundamental: dict, technical: dict) -> str:
        """生成股票分析提示词

        Args:
            symbol: 股票代码
            fundamental: 基本面数据字典
            technical: 技术面数据字典

        Returns:
            str: 格式化的提示词
        """
        fund_text = "\n".join([f"- {k}: {v}" for k, v in fundamental.items()]) if fundamental else "暂无基本面数据"
        tech_text = "\n".join([f"- {k}: {v}" for k, v in technical.items()]) if technical else "暂无技术面数据"
        return f"""请分析以下股票并给出投资建议：

【股票代码】{symbol}

【基本面数据】
{fund_text}

【技术面数据】
{tech_text}

请给出：
1. 综合评价（2-3句话）
2. 投资建议（买入/持有/卖出）及理由
3. 风险提示
4. 建议关注的关键点位或指标"""

    @staticmethod
    def quick_question(question: str, context: str = "") -> str:
        """生成快速问题提示词

        Args:
            question: 用户问题
            context: 上下文信息

        Returns:
            str: 格式化的提示词
        """
        if context:
            return f"""基于以下背景信息：
{context}

请回答用户的问题：{question}"""
        return question
