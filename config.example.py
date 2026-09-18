class Config:
    def __init__(self):
        # Crie uma chave em https://console.groq.com/keys
        self.api_key = "gsk_sua_chave_aqui"
        self.default_model = "openai/gpt-oss-120b"
        self.wifi_password = "sua_senha_wifi"


cfg = Config()
