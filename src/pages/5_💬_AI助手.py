"""
AI助手页面
AI对话分析股票
"""


import streamlit as st

from config.settings import get_settings
from src.ai.client import AIClient
from src.analysis.fundamental import FundamentalAnalyzer
from src.analysis.technical import TechnicalAnalyzer
from src.data.repository import Repository


def init_session_state():
    """初始化会话状态"""
    if "repository" not in st.session_state:
        st.session_state.repository = Repository("sqlite:///stock_analyzer.db")

    if "ai_client" not in st.session_state:
        settings = get_settings()
        if settings.openai_api_key:
            st.session_state.ai_client = AIClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
            )
        else:
            st.session_state.ai_client = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = None


def get_stock_context(symbol: str, repo: Repository) -> dict:
    """获取股票上下文信息

    Args:
        symbol: 股票代码
        repo: 数据访问层

    Returns:
        dict: 上下文信息字典
    """
    context = {"symbol": symbol}

    # 获取最新行情
    latest_quote = repo.get_latest_quote(symbol)
    if latest_quote:
        context["price"] = float(latest_quote.close)
        context["change_pct"] = float(latest_quote.change_pct) if latest_quote.change_pct else 0

    # 获取技术分析
    tech_analyzer = TechnicalAnalyzer(repo)
    tech_report = tech_analyzer.analyze(symbol)
    if tech_report.score > 0:
        context["technical_score"] = tech_report.score
        context["trend"] = tech_report.trend.direction if tech_report.trend else "未知"

    # 获取基本面分析
    fund_analyzer = FundamentalAnalyzer(repo)
    fund_report = fund_analyzer.analyze(symbol)
    if fund_report.overall_score > 0:
        context["fundamental_score"] = fund_report.overall_score
        context["summary"] = fund_report.summary

    return context


def main():
    """主函数"""
    st.set_page_config(
        page_title="AI助手 - 股票分析系统",
        page_icon="💬",
        layout="wide",
    )

    init_session_state()
    repo = st.session_state.repository
    ai_client = st.session_state.ai_client

    st.title("💬 AI助手")
    st.markdown("---")

    # 检查AI配置
    if not ai_client:
        st.warning("""
        **AI服务未配置**

        请在 `.env` 文件中配置以下参数：
        - `OPENAI_API_KEY`: OpenAI API密钥
        - `OPENAI_BASE_URL`: API基础URL（可选）
        - `OPENAI_MODEL`: 模型名称（默认gpt-4）
        """)

        # 允许用户在页面临时配置
        with st.expander("临时配置AI服务"):
            temp_key = st.text_input("API Key", type="password")
            temp_url = st.text_input("Base URL", value="https://api.openai.com/v1")
            temp_model = st.text_input("Model", value="gpt-4")

            if st.button("连接AI服务"):
                if temp_key:
                    try:
                        st.session_state.ai_client = AIClient(
                            api_key=temp_key,
                            base_url=temp_url,
                            model=temp_model,
                        )
                        st.success("AI服务连接成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")
        return

    # 侧边栏 - 股票选择
    with st.sidebar:
        st.markdown("### 📊 分析股票")

        watchlist = repo.get_watchlist()
        symbols = [item.symbol for item in watchlist]

        input_symbol = st.text_input("股票代码", placeholder="输入股票代码")
        selected_symbol = input_symbol.upper() if input_symbol else (symbols[0] if symbols else None)

        if selected_symbol:
            st.session_state.current_symbol = selected_symbol
            st.markdown(f"**当前**: {selected_symbol}")

            # 显示股票基本信息
            latest_quote = repo.get_latest_quote(selected_symbol)
            if latest_quote:
                st.metric("最新价", f"{latest_quote.close:.2f}",
                         delta=f"{float(latest_quote.change_pct):.2f}%" if latest_quote.change_pct else None)

        st.markdown("---")

        # 快捷问题
        st.markdown("### ⚡ 快捷问题")
        quick_questions = [
            "这只股票怎么样？",
            "当前是否适合买入？",
            "主要风险有哪些？",
            "技术面分析",
            "基本面分析",
        ]

        for q in quick_questions:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state.quick_question = q

    # 主内容区
    col1, col2 = st.columns([2, 1])

    # 聊天区域
    with col1:
        st.subheader("🗣️ 对话分析")

        # 显示历史消息
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # 聊天输入
        if prompt := st.chat_input("输入您的问题..."):
            # 添加用户消息
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # 生成AI回复
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    # 如果有选中的股票，添加上下文
                    context = ""
                    if st.session_state.current_symbol:
                        stock_ctx = get_stock_context(st.session_state.current_symbol, repo)
                        context = f"当前分析股票: {stock_ctx.get('symbol', '未知')}\n"
                        if "price" in stock_ctx:
                            context += f"最新价: {stock_ctx['price']:.2f}\n"
                        if "technical_score" in stock_ctx:
                            context += f"技术评分: {stock_ctx['technical_score']}\n"
                        if "fundamental_score" in stock_ctx:
                            context += f"基本面评分: {stock_ctx['fundamental_score']}\n"

                    # 调用AI
                    if context:
                        full_prompt = f"背景信息:\n{context}\n\n用户问题: {prompt}"
                        response = ai_client.chat([], full_prompt)
                    else:
                        response = ai_client.chat(st.session_state.chat_messages[:-1], prompt)

                st.markdown(response)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

        # 处理快捷问题
        if "quick_question" in st.session_state:
            q = st.session_state.quick_question
            del st.session_state.quick_question

            if st.session_state.current_symbol:
                with st.spinner("分析中..."):
                    response = ai_client.quick_analyze(st.session_state.current_symbol, q)

                st.session_state.chat_messages.append({"role": "user", "content": f"[{st.session_state.current_symbol}] {q}"})
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
                st.rerun()

        # 清空对话
        if st.button("清空对话"):
            st.session_state.chat_messages = []
            st.rerun()

    # 右侧信息面板
    with col2:
        st.subheader("📋 股票信息")

        if st.session_state.current_symbol:
            symbol = st.session_state.current_symbol

            # 获取股票信息
            stock_info = repo.get_stock_info(symbol)
            if stock_info:
                st.markdown(f"**名称**: {stock_info.name}")
                st.markdown(f"**市场**: {stock_info.market.value}")
                if stock_info.industry:
                    st.markdown(f"**行业**: {stock_info.industry}")

            st.markdown("---")

            # 快速分析
            st.markdown("### 🚀 快速AI分析")
            if st.button("生成综合分析报告", type="primary", use_container_width=True):
                with st.spinner("AI分析中..."):
                    # 获取分析数据
                    tech_analyzer = TechnicalAnalyzer(repo)
                    tech_report = tech_analyzer.analyze(symbol)

                    fund_analyzer = FundamentalAnalyzer(repo)
                    fund_report = fund_analyzer.analyze(symbol)

                    # 准备数据
                    fundamental_data = {
                        "综合评分": fund_report.overall_score,
                        "估值评分": fund_report.valuation.score if fund_report.valuation else 0,
                        "PE": float(fund_report.valuation.pe) if fund_report.valuation and fund_report.valuation.pe else None,
                        "ROE": float(fund_report.profitability.roe_current) if fund_report.profitability and fund_report.profitability.roe_current else None,
                    }

                    technical_data = {
                        "技术评分": tech_report.score,
                        "趋势": tech_report.trend.direction if tech_report.trend else "未知",
                        "RSI": float(tech_report.indicators.rsi) if tech_report.indicators and tech_report.indicators.rsi else None,
                    }

                    # 调用AI分析
                    analysis = ai_client.analyze_stock(symbol, fundamental_data, technical_data)

                st.markdown("#### 📊 AI分析报告")
                st.markdown(analysis.summary)
                st.markdown(f"*生成时间: {analysis.generated_at.strftime('%Y-%m-%d %H:%M')}*")

            st.markdown("---")

            # 使用提示
            st.markdown("### 💡 使用提示")
            st.markdown("""
            您可以问AI关于股票的问题，例如：

            - 这只股票适合长期持有吗？
            - 现在的估值是否合理？
            - 技术面走势如何？
            - 有哪些潜在风险？
            - 和同行业公司相比如何？
            """)
        else:
            st.info("请在左侧选择或输入股票代码")


if __name__ == "__main__":
    main()
