import os
from threading import Lock

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


LOCAL_MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
_GENERATOR = None
_INIT_LOCK = Lock()
_INIT_FAILED = False
_INIT_ERROR = None


def _build_generator():
    tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL_NAME)
    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
    return pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )


def get_local_generator():
    global _GENERATOR, _INIT_FAILED, _INIT_ERROR
    if _GENERATOR is not None:
        return _GENERATOR
    if _INIT_FAILED:
        raise RuntimeError(f"Local model init failed: {_INIT_ERROR}")
    with _INIT_LOCK:
        if _GENERATOR is not None:
            return _GENERATOR
        try:
            _GENERATOR = _build_generator()
            return _GENERATOR
        except Exception as e:  # noqa: BLE001
            _INIT_FAILED = True
            _INIT_ERROR = str(e)
            raise


def warmup_local_llm():
    get_local_generator()


def generate_local_answer(history: str, graph_context: str, message: str) -> str:
    generator = get_local_generator()
    prompt = (
        "You are a helpful assistant.\n"
        f"Past Dialogue Context:\n{history}\n\n"
        f"Knowledge Graph Context:\n{graph_context}\n\n"
        f"Current User Message:\n{message}\n\n"
        "Answer in a concise and helpful way:"
    )
    output = generator(
        prompt,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
    )
    generated = output[0]["generated_text"]
    if generated.startswith(prompt):
        generated = generated[len(prompt):]
    return generated.strip() or "Извините, не удалось сгенерировать ответ."
