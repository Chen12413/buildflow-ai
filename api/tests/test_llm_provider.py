import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.provider import AliyunBailianLLMProvider, DEFAULT_BAILIAN_MODEL, MockLLMProvider, get_llm_provider


class ExampleDocument(BaseModel):
    value: str


def test_get_mock_provider():
    provider = get_llm_provider(Settings(llm_provider="mock", llm_model="mock-buildflow-v1"))
    assert isinstance(provider, MockLLMProvider)


def test_get_bailian_provider_from_alias():
    provider = get_llm_provider(Settings(llm_provider="dashscope", llm_model="qwen3.5-plus", llm_api_mode="auto", DASHSCOPE_API_KEY="test-key"))
    assert isinstance(provider, AliyunBailianLLMProvider)


def test_bailian_provider_requires_api_key():
    settings = Settings(llm_provider="aliyun_bailian", llm_model="qwen3.5-plus", llm_api_mode="auto", DASHSCOPE_API_KEY=None)
    with pytest.raises(ValueError, match="bailian_api_key_required"):
        get_llm_provider(settings)


def test_bailian_provider_uses_default_model_when_mock_model_is_left_unchanged():
    settings = Settings(llm_provider="aliyun_bailian", llm_model="mock-buildflow-v1", llm_api_mode="auto", DASHSCOPE_API_KEY="test-key")
    provider = get_llm_provider(settings)
    assert isinstance(provider, AliyunBailianLLMProvider)
    assert provider.model == DEFAULT_BAILIAN_MODEL
    assert hasattr(provider.chat_client.chat.completions, "parse")


def test_bailian_auto_mode_falls_back_to_chat(monkeypatch):
    provider = get_llm_provider(Settings(llm_provider="aliyun_bailian", llm_model="qwen3.5-plus", llm_api_mode="auto", DASHSCOPE_API_KEY="test-key"))
    calls = {"responses": 0, "chat": 0}

    def fake_responses(system_prompt, user_prompt, schema):
        calls["responses"] += 1
        raise ValueError("bailian_parse_failed")

    def fake_chat(system_prompt, user_prompt, schema):
        calls["chat"] += 1
        return ExampleDocument(value="ok")

    monkeypatch.setattr(provider, "_parse_with_responses", fake_responses)
    monkeypatch.setattr(provider, "_parse_with_chat", fake_chat)

    document = provider._generate_structured_document("sys", "user", ExampleDocument)
    assert document.value == "ok"
    assert calls == {"responses": 1, "chat": 1}


def test_bailian_responses_mode_does_not_fall_back(monkeypatch):
    provider = get_llm_provider(Settings(llm_provider="aliyun_bailian", llm_model="qwen3.5-plus", llm_api_mode="responses", DASHSCOPE_API_KEY="test-key"))
    calls = {"responses": 0, "chat": 0}

    def fake_responses(system_prompt, user_prompt, schema):
        calls["responses"] += 1
        raise ValueError("bailian_parse_failed")

    def fake_chat(system_prompt, user_prompt, schema):
        calls["chat"] += 1
        return ExampleDocument(value="unexpected")

    monkeypatch.setattr(provider, "_parse_with_responses", fake_responses)
    monkeypatch.setattr(provider, "_parse_with_chat", fake_chat)

    with pytest.raises(ValueError, match="bailian_parse_failed"):
        provider._generate_structured_document("sys", "user", ExampleDocument)

    assert calls == {"responses": 1, "chat": 0}