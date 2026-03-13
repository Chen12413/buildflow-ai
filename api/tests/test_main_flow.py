def create_project(client):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "BuildFlow AI",
            "idea": "一个帮助用户把产品想法变成 PRD 的 AI 工具",
            "target_user": "独立开发者、产品经理",
            "platform": "web",
            "constraints": "一天内完成 MVP",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_create_project(client):
    payload = create_project(client)
    assert payload["name"] == "BuildFlow AI"
    assert payload["platform"] == "web"


def test_create_project_strips_timestamp_suffix(client):
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "AI 旅游规划助手 1741812345678",
            "idea": "一个帮助用户把产品想法变成 PRD 的 AI 工具",
            "target_user": "独立开发者、产品经理",
            "platform": "web",
            "constraints": "一天内完成 MVP",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["name"] == "AI 旅游规划助手"


def test_clarification_generation_and_answer_save(client):
    project = create_project(client)
    project_id = project["id"]

    clarification_response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate", json={})
    assert clarification_response.status_code == 200
    clarification_data = clarification_response.json()["data"]
    assert clarification_data["run"]["status"] == "completed"
    assert len(clarification_data["questions"]) >= 3

    answer_response = client.put(
        f"/api/v1/projects/{project_id}/clarifications/answers",
        json={
            "answers": [
                {
                    "question_id": clarification_data["questions"][0]["id"],
                    "answer": "帮助用户在 10 分钟内得到结构化 PRD",
                }
            ]
        },
    )
    assert answer_response.status_code == 200
    assert answer_response.json()["data"]["saved_count"] == 1


def test_clarification_generation_is_idempotent_for_existing_questions(client):
    project = create_project(client)
    project_id = project["id"]

    first_response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate", json={})
    second_response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate", json={})

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_questions = first_response.json()["data"]["questions"]
    second_questions = second_response.json()["data"]["questions"]

    assert [item["id"] for item in second_questions] == [item["id"] for item in first_questions]
    assert second_response.json()["data"]["run"]["status"] == "completed"


def test_full_generation_chain_and_export(client):
    project = create_project(client)
    project_id = project["id"]

    clarification_response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate", json={})
    questions = clarification_response.json()["data"]["questions"]

    client.put(
        f"/api/v1/projects/{project_id}/clarifications/answers",
        json={
            "answers": [
                {"question_id": question["id"], "answer": f"回答 {index}"}
                for index, question in enumerate(questions, start=1)
            ]
        },
    )

    prd_generation_response = client.post(f"/api/v1/projects/{project_id}/prd/generate", json={})
    assert prd_generation_response.status_code == 202
    prd_run_id = prd_generation_response.json()["data"]["run"]["id"]

    prd_run_response = client.get(f"/api/v1/runs/{prd_run_id}")
    assert prd_run_response.status_code == 200
    assert prd_run_response.json()["data"]["status"] == "completed"

    prd_artifact_response = client.get(f"/api/v1/projects/{project_id}/artifacts/prd/latest")
    assert prd_artifact_response.status_code == 200
    prd_artifact = prd_artifact_response.json()["data"]
    assert prd_artifact["type"] == "prd"
    assert prd_artifact["content_json"]["mvp_goal"]

    prd_export_response = client.get(f"/api/v1/projects/{project_id}/export/markdown")
    assert prd_export_response.status_code == 200
    assert "BuildFlow AI PRD" in prd_export_response.text

    planning_generation_response = client.post(f"/api/v1/projects/{project_id}/planning/generate", json={})
    assert planning_generation_response.status_code == 202
    planning_run_id = planning_generation_response.json()["data"]["run"]["id"]

    planning_run_response = client.get(f"/api/v1/runs/{planning_run_id}")
    assert planning_run_response.status_code == 200
    assert planning_run_response.json()["data"]["status"] == "completed"

    planning_artifact_response = client.get(f"/api/v1/projects/{project_id}/artifacts/planning/latest")
    assert planning_artifact_response.status_code == 200
    planning_artifact = planning_artifact_response.json()["data"]
    assert planning_artifact["type"] == "planning"
    assert len(planning_artifact["content_json"]["milestones"]) >= 1

    planning_export_response = client.get(f"/api/v1/projects/{project_id}/export/planning/markdown")
    assert planning_export_response.status_code == 200
    assert "BuildFlow AI Planning" in planning_export_response.text

    task_breakdown_generation_response = client.post(f"/api/v1/projects/{project_id}/task-breakdown/generate", json={})
    assert task_breakdown_generation_response.status_code == 202
    task_breakdown_run_id = task_breakdown_generation_response.json()["data"]["run"]["id"]

    task_breakdown_run_response = client.get(f"/api/v1/runs/{task_breakdown_run_id}")
    assert task_breakdown_run_response.status_code == 200
    assert task_breakdown_run_response.json()["data"]["status"] == "completed"

    task_breakdown_artifact_response = client.get(f"/api/v1/projects/{project_id}/artifacts/task-breakdown/latest")
    assert task_breakdown_artifact_response.status_code == 200
    task_breakdown_artifact = task_breakdown_artifact_response.json()["data"]
    assert task_breakdown_artifact["type"] == "task_breakdown"
    assert len(task_breakdown_artifact["content_json"]["modules"]) >= 1

    task_breakdown_export_response = client.get(f"/api/v1/projects/{project_id}/export/task-breakdown/markdown")
    assert task_breakdown_export_response.status_code == 200
    assert "BuildFlow AI Task Breakdown" in task_breakdown_export_response.text

    demo_generation_response = client.post(f"/api/v1/projects/{project_id}/demo/generate", json={})
    assert demo_generation_response.status_code == 202
    demo_run_id = demo_generation_response.json()["data"]["run"]["id"]

    demo_run_response = client.get(f"/api/v1/runs/{demo_run_id}")
    assert demo_run_response.status_code == 200
    assert demo_run_response.json()["data"]["status"] == "completed"

    demo_artifact_response = client.get(f"/api/v1/projects/{project_id}/artifacts/demo/latest")
    assert demo_artifact_response.status_code == 200
    demo_artifact = demo_artifact_response.json()["data"]
    assert demo_artifact["type"] == "demo"
    assert len(demo_artifact["content_json"]["screens"]) >= 1
    assert len(demo_artifact["content_json"]["agent_cards"]) >= 2

    demo_export_response = client.get(f"/api/v1/projects/{project_id}/export/demo/markdown")
    assert demo_export_response.status_code == 200
    assert "BuildFlow AI Demo Blueprint" in demo_export_response.text


def test_demo_generation_falls_back_to_local_template_when_bailian_times_out(client, monkeypatch):
    demo_workflow_module = __import__("app.workflows.demo_workflow", fromlist=["DemoWorkflow"])
    project = create_project(client)
    project_id = project["id"]

    clarification_response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate", json={})
    questions = clarification_response.json()["data"]["questions"]
    client.put(
        f"/api/v1/projects/{project_id}/clarifications/answers",
        json={
            "answers": [
                {"question_id": question["id"], "answer": f"回答 {index}"}
                for index, question in enumerate(questions, start=1)
            ]
        },
    )

    assert client.post(f"/api/v1/projects/{project_id}/prd/generate", json={}).status_code == 202
    assert client.post(f"/api/v1/projects/{project_id}/planning/generate", json={}).status_code == 202
    assert client.post(f"/api/v1/projects/{project_id}/task-breakdown/generate", json={}).status_code == 202

    class TimeoutDemoProvider:
        def generate_demo_blueprint_document(self, project, prd_document, planning_document, task_breakdown_document, answers):
            raise ValueError("bailian_timeout")

    monkeypatch.setattr(demo_workflow_module, "get_llm_provider", lambda: TimeoutDemoProvider())

    demo_generation_response = client.post(f"/api/v1/projects/{project_id}/demo/generate", json={})
    assert demo_generation_response.status_code == 202
    demo_run_id = demo_generation_response.json()["data"]["run"]["id"]

    demo_run_response = client.get(f"/api/v1/runs/{demo_run_id}")
    assert demo_run_response.status_code == 200
    assert demo_run_response.json()["data"]["status"] == "completed"

    demo_artifact_response = client.get(f"/api/v1/projects/{project_id}/artifacts/demo/latest")
    assert demo_artifact_response.status_code == 200
    demo_artifact = demo_artifact_response.json()["data"]
    assert demo_artifact["type"] == "demo"
    assert len(demo_artifact["content_json"]["screens"]) >= 1
    assert all(card["model_used"] == "local-fallback" for card in demo_artifact["content_json"]["agent_cards"])
