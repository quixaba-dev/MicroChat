import socket
import ssl
import ujson
import utime

from config import cfg


class GroqAgent:
    """Cliente Groq com memória de conversa separada por usuário."""

    def __init__(self):
        self.model = cfg.default_model
        self.sessions = {}
        self.max_messages = 12
        self.session_ttl = 60 * 60 * 6

    def _prune_sessions(self):
        now = utime.time()
        expired = []
        for user_id, session in self.sessions.items():
            if now - session["updated_at"] > self.session_ttl:
                expired.append(user_id)
        for user_id in expired:
            del self.sessions[user_id]

    def _get_messages(self, user_id):
        self._prune_sessions()
        if user_id not in self.sessions:
            self.sessions[user_id] = {"messages": [], "updated_at": utime.time()}
        return self.sessions[user_id]["messages"]

    def clear_session(self, user_id):
        if user_id in self.sessions:
            del self.sessions[user_id]

    def _https_post(self, host, path, headers, body):
        addr = socket.getaddrinfo(host, 443)[0][-1]
        sock = socket.socket()
        try:
            sock.connect(addr)
            sock = ssl.wrap_socket(sock, server_hostname=host)
            request = "POST {} HTTP/1.1\r\nHost: {}\r\n".format(path, host)
            for key, value in headers.items():
                request += "{}: {}\r\n".format(key, value)
            request += "Content-Length: {}\r\nConnection: close\r\n\r\n".format(len(body))
            sock.write(request.encode("utf-8") + body)
            response = b""
            while True:
                chunk = sock.read(1024)
                if not chunk:
                    break
                response += chunk
            return response
        finally:
            try:
                sock.close()
            except:
                pass

    def _decode_chunked(self, body):
        """Converte resposta HTTP chunked em bytes de JSON."""
        decoded = b""
        while body:
            line_end = body.find(b"\r\n")
            if line_end == -1:
                raise Exception("Resposta chunked invalida")
            size = int(body[:line_end], 16)
            if size == 0:
                return decoded
            start = line_end + 2
            end = start + size
            if len(body) < end:
                raise Exception("Chunk incompleto")
            decoded += body[start:end]
            body = body[end + 2:]
        raise Exception("Resposta chunked incompleta")

    def generate_response(self, user_id, prompt):
        messages = self._get_messages(user_id)
        messages.append({"role": "user", "content": prompt})
        try:
            payload = {"model": self.model, "messages": messages}
            body = ujson.dumps(payload).encode("utf-8")
            headers = {"Authorization": "Bearer " + cfg.api_key, "Content-Type": "application/json"}
            raw_response = self._https_post("api.groq.com", "/openai/v1/chat/completions", headers, body)
            separator = raw_response.find(b"\r\n\r\n")
            if separator == -1:
                raise Exception("Resposta HTTP invalida")
            response_headers = raw_response[:separator].lower()
            response_body = raw_response[separator + 4:]
            if b"transfer-encoding: chunked" in response_headers:
                response_body = self._decode_chunked(response_body)
            try:
                data = ujson.loads(response_body)
            except ValueError:
                print("Groq status:", raw_response[:separator].split(b"\r\n")[0])
                print("Groq body:", response_body[:300])
                raise Exception("JSON invalido na resposta do Groq")
            if "error" in data:
                raise Exception(str(data["error"]))
            answer = data["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": answer})
            if len(messages) > self.max_messages:
                del messages[:-self.max_messages]
            self.sessions[user_id]["updated_at"] = utime.time()
            return answer
        except Exception:
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            raise
