import json
import os
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

UPSTREAM = "https://glm-ai.chat"
USER_AGENT = os.getenv(
    "UPSTREAM_USER_AGENT",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
)
MAX_CHARS = 8000
TEXT_MODELS = {
    "glm-5.3", "glm-5.3-flash", "glm-5.2", "glm-5.1", "glm-4.7",
    "glm-4.6", "glm-4.5", "glm-4.7-flash", "glm-4.5-flash", "glm-4.7-flashx",
}
ALL_MODELS = TEXT_MODELS | {"glm-image"}

app = FastAPI(title="MandoAI", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    model: str = Field(default="glm-5.3-flash", min_length=1, max_length=40)
    messages: list[dict] = Field(min_length=1, max_length=60)


@app.get("/")
async def home():
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "MandoAI"}


def sse(event: dict) -> bytes:
    return ("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode("utf-8")


@app.post("/api/chat")
async def chat(body: ChatRequest):
    if body.model not in ALL_MODELS:
        raise HTTPException(status_code=400, detail="النموذج غير موجود في القائمة.")
    if body.model == "glm-image":
        raise HTTPException(
            status_code=501,
            detail="glm-image غير قابل للتشغيل حاليًا: مسار إنشاء الصور في السكربت الأصلي معطّل ولم يتم التحقق من واجهته.",
        )

    clean_messages = []
    for item in body.messages:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            raise HTTPException(status_code=400, detail="صيغة الرسائل غير صحيحة.")
        if len(content) > MAX_CHARS:
            raise HTTPException(status_code=413, detail=f"الحد الأقصى للرسالة {MAX_CHARS} حرف.")
        clean_messages.append({"role": role, "content": content})

    async def generate() -> AsyncIterator[bytes]:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Origin": UPSTREAM,
            "Referer": UPSTREAM + "/",
            "X-Requested-With": "com.duckduckgo.mobile.android",
        }
        try:
            timeout = httpx.Timeout(180.0, connect=15.0)
            async with httpx.AsyncClient(
                base_url=UPSTREAM,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                session = await client.get(
                    "/wp-json/glm-chat/v1/session",
                    headers={
                        "Accept": "application/json",
                        "X-Requested-With": headers["X-Requested-With"],
                        "Referer": headers["Referer"],
                    },
                )
                session.raise_for_status()
                nonce = session.json().get("nonce")
                if not nonce:
                    yield sse({"type": "error", "message": "لم يتم استلام رمز الجلسة من الخدمة."})
                    return
                headers["X-GLM-Nonce"] = nonce
                async with client.stream(
                    "POST",
                    "/wp-json/glm-chat/v1/message",
                    json={"model": body.model, "messages": clean_messages},
                    headers=headers,
                ) as response:
                    if response.status_code == 403:
                        yield sse({"type": "error", "message": "رفضت الخدمة الطلب (403). قد تكون الجلسة أو صلاحية الخدمة غير متاحة."})
                        return
                    if response.status_code != 200:
                        detail = (await response.aread()).decode("utf-8", "replace")[:500]
                        yield sse({"type": "error", "message": f"الخدمة أعادت HTTP {response.status_code}: {detail}"})
                        return
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n\n" in buffer:
                            raw_event, buffer = buffer.split("\n\n", 1)
                            for line in raw_event.splitlines():
                                if not line.startswith("data:"):
                                    continue
                                data = line[5:].strip()
                                if not data or data == "[DONE]":
                                    continue
                                try:
                                    parsed = json.loads(data)
                                except json.JSONDecodeError:
                                    continue
                                yield sse(parsed)
        except httpx.TimeoutException:
            yield sse({"type": "error", "message": "انتهت مهلة الاتصال بالخدمة. حاول مرة أخرى."})
        except httpx.HTTPError as exc:
            yield sse({"type": "error", "message": f"تعذر الاتصال بالخدمة: {str(exc)[:300]}"})
        except Exception:
            yield sse({"type": "error", "message": "حدث خطأ غير متوقع أثناء معالجة الطلب."})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
