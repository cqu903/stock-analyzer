"""
AI客户端测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.ai.client import AIClient
from src.ai.prompts import Prompts
from src.models.schemas import AIAnalysis


class TestPrompts:
    """提示词模板测试"""

    def test_system_analyst_exists(self):
        """测试系统提示词存在"""
        assert Prompts.SYSTEM_ANALYST is not None
        assert "股票分析师" in Prompts.SYSTEM_ANALYST

    def test_stock_analysis_with_data(self):
        """测试股票分析提示词生成（有数据）"""
        fundamental = {"PE": 15.5, "ROE": 12.3}
        technical = {"MA5": 10.2, "MACD": "金叉"}

        prompt = Prompts.stock_analysis("000001.SZ", fundamental, technical)

        assert "000001.SZ" in prompt
        assert "PE" in prompt
        assert "ROE" in prompt
        assert "MA5" in prompt
        assert "MACD" in prompt
        assert "基本面数据" in prompt
        assert "技术面数据" in prompt

    def test_stock_analysis_empty_data(self):
        """测试股票分析提示词生成（空数据）"""
        prompt = Prompts.stock_analysis("000001.SZ", {}, {})

        assert "000001.SZ" in prompt
        assert "暂无基本面数据" in prompt
        assert "暂无技术面数据" in prompt

    def test_quick_question_with_context(self):
        """测试快速问题提示词（有上下文）"""
        prompt = Prompts.quick_question("这只股票怎么样？", "PE=15, ROE=20%")

        assert "这只股票怎么样？" in prompt
        assert "PE=15, ROE=20%" in prompt

    def test_quick_question_without_context(self):
        """测试快速问题提示词（无上下文）"""
        question = "什么是MACD？"
        prompt = Prompts.quick_question(question, "")

        assert prompt == question


class TestAIClient:
    """AI客户端测试"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI客户端"""
        with patch("src.ai.client.OpenAI") as mock:
            yield mock

    @pytest.fixture
    def ai_client(self, mock_openai_client):
        """创建AI客户端实例"""
        return AIClient(
            api_key="test_key",
            base_url="https://api.test.com/v1",
            model="gpt-4",
        )

    def test_init(self, mock_openai_client):
        """测试初始化"""
        client = AIClient(
            api_key="test_key",
            base_url="https://api.test.com/v1",
            model="gpt-3.5-turbo",
        )

        mock_openai_client.assert_called_once_with(
            api_key="test_key",
            base_url="https://api.test.com/v1",
        )
        assert client.model == "gpt-3.5-turbo"

    def test_analyze_stock_success(self, ai_client, mock_openai_client):
        """测试股票分析成功"""
        # 设置Mock返回值
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="这是一条分析报告"))]
        ai_client.client.chat.completions.create.return_value = mock_response

        result = ai_client.analyze_stock(
            symbol="000001.SZ",
            fundamental={"PE": 15},
            technical={"MA5": 10},
        )

        assert isinstance(result, AIAnalysis)
        assert result.symbol == "000001.SZ"
        assert result.summary == "这是一条分析报告"
        assert result.confidence == 80

    def test_analyze_stock_failure(self, ai_client):
        """测试股票分析失败"""
        ai_client.client.chat.completions.create.side_effect = Exception("API Error")

        result = ai_client.analyze_stock(
            symbol="000001.SZ",
            fundamental={},
            technical={},
        )

        assert isinstance(result, AIAnalysis)
        assert result.symbol == "000001.SZ"
        assert "分析失败" in result.summary
        assert result.confidence == 0

    def test_chat_success(self, ai_client):
        """测试对话成功"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="这是AI的回复"))]
        ai_client.client.chat.completions.create.return_value = mock_response

        messages = [{"role": "user", "content": "你好"}]
        result = ai_client.chat(messages, "请分析一下这只股票")

        assert result == "这是AI的回复"
        # 验证调用参数包含历史消息和新消息
        call_args = ai_client.client.chat.completions.create.call_args
        assert len(call_args.kwargs["messages"]) == 2

    def test_chat_failure(self, ai_client):
        """测试对话失败"""
        ai_client.client.chat.completions.create.side_effect = Exception("Network Error")

        result = ai_client.chat([], "你好")

        assert "抱歉" in result
        assert "Network Error" in result

    def test_quick_analyze_success(self, ai_client):
        """测试快速分析成功"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="快速分析结果"))]
        ai_client.client.chat.completions.create.return_value = mock_response

        result = ai_client.quick_analyze("000001.SZ", "这只股票值得买入吗？")

        assert result == "快速分析结果"

    def test_quick_analyze_failure(self, ai_client):
        """测试快速分析失败"""
        ai_client.client.chat.completions.create.side_effect = Exception("Timeout")

        result = ai_client.quick_analyze("000001.SZ", "分析一下")

        assert "分析失败" in result


class TestAIAnalysis:
    """AI分析结果模型测试"""

    def test_create_ai_analysis(self):
        """测试创建AI分析结果"""
        analysis = AIAnalysis(
            symbol="000001.SZ",
            summary="这是一只值得关注的股票",
            generated_at=datetime.now(),
            confidence=85,
        )

        assert analysis.symbol == "000001.SZ"
        assert analysis.summary == "这是一只值得关注的股票"
        assert analysis.confidence == 85
        assert analysis.recommendation is None
        assert analysis.risks == []

    def test_ai_analysis_with_all_fields(self):
        """测试创建完整AI分析结果"""
        analysis = AIAnalysis(
            symbol="000001.SZ",
            summary="综合分析结果",
            generated_at=datetime.now(),
            recommendation="持有",
            risks=["市场波动风险", "行业政策风险"],
            confidence=75,
        )

        assert analysis.recommendation == "持有"
        assert len(analysis.risks) == 2
