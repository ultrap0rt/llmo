# AI Knowledge Graph Memory System

Эта ИИ-система использует архитектуру GraphRAG и векторную память (Episodic Memory) для обеспечения "бесконечного контекста" и непрерывного пополнения графа знаний.

## Стек

- **Main LLM**: DeepSeek-R1/V3 (через Ollama).
- **Knowledge Extractor**: Qwen 2.5 (или другая быстрая модель через Ollama).
- **Graph DB**: Neo4j.
- **Vector DB**: Qdrant.
- **Backend**: FastAPI + LangChain.

## Запуск

1. **Запуск инфраструктуры:**
   ```bash
   docker-compose up -d
   ```

2. **Загрузка моделей в Ollama:**
   ```bash
   docker exec -it <ollama_container_id> ollama run deepseek-r1:1.5b
   docker exec -it <ollama_container_id> ollama run qwen2.5:0.5b
   ```

3. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск API:**
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

5. **Тестирование:**
   ```bash
   python test_client.py
   ```
   В `test_client.py` заложен скрипт, имитирующий долгую паузу между сообщениями:
   - Шаг 1: Пользователь сообщает факт о "Project X".
   - Шаг 2: В фоновом режиме срабатывает `extractor.py` и сохраняет сущности (Project X) и связи в Neo4j, а также обновляет Qdrant.
   - Шаг 3: Имитация паузы.
   - Шаг 4: Пользователь возвращается и спрашивает о проекте. Система находит векторные записи и графовые связи в Neo4j, предоставляя полный ответ.
