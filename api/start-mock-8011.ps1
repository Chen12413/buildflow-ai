$env:LLM_PROVIDER='mock'
$env:LLM_MODEL='mock-buildflow-v1'
$env:LLM_API_MODE='auto'
$env:DATABASE_URL='sqlite+pysqlite:///./buildflow.mock.db'
& 'd:/OneDrive/Desktop/vibecoding/api/.venv/Scripts/python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8011
