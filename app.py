import json
import os
import re
import sys
import uuid

from flask import Flask, Response, jsonify, render_template, request, session

from config import DEFAULT_API_BASE, DEFAULT_API_KEY, DEFAULT_MODEL
from scenes import SCENES, STICKERS, scene_prompt
from models import LLMClient
from prompts import MODEL_A_SYSTEM, MODEL_B_SYSTEM, MODEL_C_SYSTEM

# When bundled by PyInstaller, resources are extracted to a temp dir
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.secret_key = "healthchat-secret-" + uuid.uuid4().hex

# In-memory chat history storage keyed by session id
chat_histories = {}
# Keep credentials on the server, never in Flask's client-readable session cookie.
model_configs = {}


def get_session_id():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


def get_config():
    """Return server-side configuration for this browser, or local defaults."""
    return model_configs.get(get_session_id(), {
        "model_a": {"api_base": DEFAULT_API_BASE, "api_key": DEFAULT_API_KEY, "model": DEFAULT_MODEL},
        "model_b": {"api_base": DEFAULT_API_BASE, "api_key": DEFAULT_API_KEY, "model": DEFAULT_MODEL},
        "model_c": {"api_base": DEFAULT_API_BASE, "api_key": DEFAULT_API_KEY, "model": DEFAULT_MODEL},
    })


def make_client(cfg):
    return LLMClient(cfg["api_base"], cfg["api_key"], cfg["model"])


def parse_model_a_response(raw):
    """Split Model A's response into user-visible text and monitor data."""
    # Try to find [MONITOR] block with json
    monitor_match = re.search(
        r'\[MONITOR\]\s*```json\s*(\{.*?\})\s*```',
        raw, re.DOTALL
    )
    if not monitor_match:
        # Fallback: try without code fence
        monitor_match = re.search(
            r'\[MONITOR\]\s*(\{.*?\})',
            raw, re.DOTALL
        )

    if monitor_match:
        response_text = raw[:monitor_match.start()].strip()
        response_text = re.sub(r'^\[RESPONSE\]\s*', '', response_text).strip()
        try:
            monitor = json.loads(monitor_match.group(1))
            return response_text, monitor
        except json.JSONDecodeError:
            return response_text, None
    # No monitor block found
    clean = re.sub(r'^\[RESPONSE\]\s*', '', raw).strip()
    # Strip any stray monitor tags
    clean = re.sub(r'\[MONITOR\].*', '', clean, flags=re.DOTALL).strip()
    return clean, None


def parse_json_from_llm(raw):
    """Extract a JSON object from LLM output, trying multiple strategies."""
    # Strategy 1: code fence
    m = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Strategy 2: first { ... }
    m = re.search(r'(\{.*\})', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def sse_event(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.route("/")
def index():
    return render_template("index.html", scenes=SCENES, stickers=STICKERS)


@app.route("/api/config", methods=["GET"])
def get_config_route():
    cfg = get_config()
    # Mask API keys for display
    masked = {}
    for k, v in cfg.items():
        masked[k] = {
            "api_base": v["api_base"],
            "api_key": "已配置（留空保留）" if v["api_key"] else "",
            "api_key_set": bool(v["api_key"]),
            "model": v["model"],
        }
    return jsonify(masked)


@app.route("/api/config", methods=["POST"])
def set_config_route():
    data = request.json
    if data.get("reset") is True:
        model_configs.pop(get_session_id(), None)
        return jsonify({"status": "ok"})
    cfg = get_config()
    for model_key in ["model_a", "model_b", "model_c"]:
        if model_key in data:
            for field in ["api_base", "api_key", "model"]:
                if field in data[model_key] and data[model_key][field]:
                    cfg[model_key][field] = data[model_key][field]
    model_configs[get_session_id()] = cfg
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    sid = get_session_id()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "请求格式错误"}), 400
    scene_id = data.get("scene", "tea")
    sticker_id = data.get("sticker")
    if not isinstance(scene_id, str) or scene_id not in SCENES:
        return jsonify({"error": "未知情景"}), 400
    if sticker_id is not None and (not isinstance(sticker_id, str) or sticker_id not in STICKERS):
        return jsonify({"error": "未知贴图"}), 400
    message = data.get("message", "")
    if not isinstance(message, str):
        return jsonify({"error": "消息须为文字"}), 400
    user_msg = f"[发送贴图：{STICKERS[sticker_id]}]" if sticker_id else message.strip()
    if not user_msg:
        return jsonify({"error": "empty message"}), 400

    if sid not in chat_histories:
        chat_histories[sid] = []
    history = chat_histories[sid]
    history.append({"role": "user", "content": user_msg})

    cfg = get_config()

    def generate():
        # Step 1: Call Model A
        if not cfg["model_a"]["api_key"]:
            yield sse_event("error", {"text": "请先打开右上角设置，填写聊天模型的 API Key，再开始对话。"})
            yield sse_event("done", {})
            return
        client_a = make_client(cfg["model_a"])
        messages_a = [{"role": "system", "content": MODEL_A_SYSTEM + scene_prompt(scene_id)}] + history
        raw_a = client_a.chat_sync(messages_a)

        if raw_a.startswith("[ERROR]"):
            yield sse_event("error", {"text": raw_a})
            yield sse_event("done", {})
            return

        app.logger.info("=== Model A raw response ===\n%s", raw_a)

        response_text, monitor = parse_model_a_response(raw_a)
        app.logger.info("=== Parsed: text=%s, monitor=%s ===", response_text[:80], monitor)
        history.append({"role": "assistant", "content": response_text})

        yield sse_event("assistant_message", {"text": response_text})

        detected = (monitor or {}).get("detected", "none")
        reason = (monitor or {}).get("reason", "")

        if detected == "psychological":
            yield sse_event("thinking", {"status": "正在进行心理健康评估..."})

            # Collect up to 10 recent messages
            recent = history[-10:]
            context_text = "\n".join(
                f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in recent
            )
            prompt_for_b = f"以下是用户的近期聊天记录：\n\n{context_text}\n\n初步分析原因：{reason}\n\n请分析并给出你的判断。"

            client_b = make_client(cfg["model_b"])
            raw_b = client_b.chat_sync([
                {"role": "system", "content": MODEL_B_SYSTEM},
                {"role": "user", "content": prompt_for_b},
            ])
            result_b = parse_json_from_llm(raw_b)

            if result_b:
                intervention = result_b.get("intervention", "none")
                msg_to_user = result_b.get("message_to_user", "")

                if intervention in ("suggest", "force"):
                    yield sse_event("intervention", {
                        "type": intervention,
                        "message": msg_to_user,
                        "reasoning": result_b.get("reasoning", ""),
                    })
                    history.append({"role": "assistant", "content": msg_to_user})
            else:
                yield sse_event("intervention", {
                    "type": "suggest",
                    "message": "我们注意到您可能正在经历一些心理压力，建议您考虑与专业心理咨询师交流。",
                    "reasoning": reason,
                })

        elif detected == "health":
            yield sse_event("thinking", {"status": "正在分析健康状况..."})

            # Collect up to 25 recent messages
            recent = history[-25:]
            context_text = "\n".join(
                f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in recent
            )
            prompt_for_c = f"以下是用户的近期聊天记录：\n\n{context_text}\n\n初步分析原因：{reason}\n\n请分析并给出健康建议。"

            client_c = make_client(cfg["model_c"])
            raw_c = client_c.chat_sync([
                {"role": "system", "content": MODEL_C_SYSTEM},
                {"role": "user", "content": prompt_for_c},
            ])
            result_c = parse_json_from_llm(raw_c)

            if result_c:
                msg_to_user = result_c.get("message_to_user", result_c.get("advice", ""))
                yield sse_event("health_advice", {
                    "message": msg_to_user,
                    "severity": result_c.get("severity", "minor"),
                })
                history.append({"role": "assistant", "content": msg_to_user})
            else:
                yield sse_event("health_advice", {
                    "message": "请注意身体健康，如有需要请及时就医。",
                    "severity": "minor",
                })

        yield sse_event("done", {})

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    sid = get_session_id()
    chat_histories.pop(sid, None)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    debug = not getattr(sys, 'frozen', False)
    app.run(debug=debug, host="127.0.0.1", port=5000)
