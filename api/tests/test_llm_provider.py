from datetime import datetime

import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.provider import AliyunBailianLLMProvider, DEFAULT_BAILIAN_MODEL, MockLLMProvider, get_llm_provider
from app.schemas.project import Platform, ProjectRead


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


def test_bailian_auto_mode_falls_back_to_chat_on_request_failed(monkeypatch):
    provider = get_llm_provider(Settings(llm_provider="aliyun_bailian", llm_model="qwen3.5-plus", llm_api_mode="auto", DASHSCOPE_API_KEY="test-key"))
    calls = {"responses": 0, "chat": 0}

    def fake_responses(system_prompt, user_prompt, schema):
        calls["responses"] += 1
        raise ValueError("bailian_request_failed")

    def fake_chat(system_prompt, user_prompt, schema):
        calls["chat"] += 1
        return ExampleDocument(value="ok")

    monkeypatch.setattr(provider, "_parse_with_responses", fake_responses)
    monkeypatch.setattr(provider, "_parse_with_chat", fake_chat)

    document = provider._generate_structured_document("sys", "user", ExampleDocument)
    assert document.value == "ok"
    assert calls == {"responses": 1, "chat": 1}


def test_bailian_auto_mode_falls_back_to_chat_on_timeout(monkeypatch):
    provider = get_llm_provider(Settings(llm_provider="aliyun_bailian", llm_model="qwen3.5-plus", llm_api_mode="auto", DASHSCOPE_API_KEY="test-key"))
    calls = {"responses": 0, "chat": 0}

    def fake_responses(system_prompt, user_prompt, schema):
        calls["responses"] += 1
        raise ValueError("bailian_timeout")

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


def test_mock_provider_generates_task_breakdown_and_demo():
    provider = MockLLMProvider()
    project = ProjectRead(
        id="project-1",
        name="BuildFlow AI",
        idea="Turn product ideas into a maintainable multi-agent delivery chain.",
        target_user="AI product managers, indie hackers",
        platform=Platform.WEB,
        constraints="Ship an MVP in one day.",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    prd_document = provider.generate_prd_document(project, ["Focus on maintainability", "Cover the full chain"])
    planning_document = provider.generate_planning_document(project, prd_document, ["Focus on maintainability", "Cover the full chain"])
    task_breakdown_document = provider.generate_task_breakdown_document(project, prd_document, planning_document, ["Need test coverage"])
    demo_document = provider.generate_demo_blueprint_document(project, prd_document, planning_document, task_breakdown_document, ["Need a good demo"])

    assert len(task_breakdown_document.modules) >= 1
    assert all(task.acceptance_criteria for module in task_breakdown_document.modules for task in module.tasks)
    assert len(demo_document.screens) >= 1
    assert len(demo_document.agent_cards) >= 2
    assert demo_document.screens[0].sample_inputs
    assert demo_document.screens[0].sample_outputs
    assert demo_document.screens[0].success_signal
    assert demo_document.screens[0].actions[0].result_preview
    assert demo_document.agent_cards[0].system_prompt_preview
    assert demo_document.agent_cards[0].user_prompt_preview
