import uasyncio as asyncio
import ujson

from wifi import Connector
from groq import GroqAgent


conn = Connector()
agent = GroqAgent()
MAX_BODY_SIZE = 4096
STATIC_FILES = {
    b"/": ("frontend/index.html", "text/html; charset=utf-8"),
    b"/style.css": ("frontend/style.css", "text/css; charset=utf-8"),
    b"/api.js": ("frontend/api.js", "application/javascript; charset=utf-8")
}


async def send_response(writer, status, data, content_type="application/json"):
    body = data if isinstance(data, bytes) else ujson.dumps(data).encode("utf-8")
    status_text = {200: "OK", 400: "Bad Request", 404: "Not Found", 413: "Payload Too Large", 500: "Internal Server Error"}.get(status, "OK")
    headers = ("HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n").format(status, status_text, content_type, len(body))
    await writer.awrite(headers.encode("utf-8"))
    await writer.awrite(body)


async def serve_static(writer, path):
    if path not in STATIC_FILES:
        await send_response(writer, 404, {"error": "Not found"})
        return
    filename, content_type = STATIC_FILES[path]
    try:
        with open(filename, "rb") as file:
            await send_response(writer, 200, file.read(), content_type)
    except OSError:
        await send_response(writer, 404, {"error": "Asset not found"})


async def handle_client(reader, writer):
    try:
        request = await reader.read(1024)
        if not request:
            return
        separator = request.find(b"\r\n\r\n")
        if separator == -1:
            await send_response(writer, 400, {"error": "Invalid HTTP request"})
            return
        header_data, body = request[:separator], request[separator + 4:]
        request_parts = header_data.split(b"\r\n")[0].split()
        if len(request_parts) < 2:
            await send_response(writer, 400, {"error": "Invalid request line"})
            return
        method, path = request_parts[0], request_parts[1].split(b"?", 1)[0]
        if method == b"OPTIONS":
            await send_response(writer, 200, b"", "text/plain")
            return
        if method == b"GET":
            await serve_static(writer, path)
            return
        if method != b"POST" or path not in (b"/api/chat", b"/api/reset"):
            await send_response(writer, 404, {"error": "Not found"})
            return
        content_length = 0
        for line in header_data.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1].strip())
                break
        if content_length <= 0 or content_length > MAX_BODY_SIZE:
            await send_response(writer, 413, {"error": "Invalid or oversized request"})
            return
        while len(body) < content_length:
            chunk = await reader.read(content_length - len(body))
            if not chunk:
                break
            body += chunk
        # O primeiro read pode receber mais dados que o body atual;
        # usa rigorosamente o Content-Length antes de decodificar.
        body = body[:content_length]
        try:
            data = ujson.loads(body)
        except ValueError:
            print("JSON de entrada invalido:", body)
            await send_response(writer, 400, {"error": "Invalid JSON payload"})
            return
        user_id = data.get("user_id", "")
        if not isinstance(user_id, str) or len(user_id) < 8 or len(user_id) > 64:
            await send_response(writer, 400, {"error": "A valid user_id is required"})
            return
        if path == b"/api/reset":
            agent.clear_session(user_id)
            await send_response(writer, 200, {"ok": True})
            return
        prompt = data.get("prompt", "").strip()
        if not prompt or len(prompt) > 2000:
            await send_response(writer, 400, {"error": "Prompt must contain up to 2000 characters"})
            return
        answer = agent.generate_response(user_id, prompt)
        await send_response(writer, 200, {"response": answer})
    except Exception as error:
        print("HTTP ERROR:", error)
        try:
            await send_response(writer, 500, {"error": "Unable to generate a response"})
        except:
            pass
    finally:
        try:
            await writer.aclose()
        except:
            pass


async def main():
    if not conn.connect():
        print("Wi-Fi não conectado.")
        return
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
    print("Server running on:", conn.wlan.ifconfig()[0])
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())
