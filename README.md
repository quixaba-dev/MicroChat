# MicroChat

Uma interface de chat de IA minimalista e responsiva, servida diretamente por um ESP32 com MicroPython e conectada à API da Groq.

![MicroChat](https://img.shields.io/badge/MicroPython-ESP32-2f7fdd?logo=micropython&logoColor=white) ![Groq](https://img.shields.io/badge/AI-Groq-b8ff57?logo=groq&logoColor=111111)

## Recursos

- Interface escura, responsiva e otimizada para celular
- Chat com envio por Enter e mensagens multiline com Shift + Enter
- Servidor HTTP assíncrono rodando no ESP32
- Histórico isolado por navegador/usuário
- Até 12 mensagens de contexto por conversa
- Limpeza automática de sessões inativas após 6 horas
- Botão para começar uma conversa nova

## Pré-requisitos

- ESP32 com MicroPython e acesso ao Wi-Fi
- Uma chave de API da [Groq](https://console.groq.com/keys)
- VS Code com a extensão MicroPico, ou outra ferramenta para copiar arquivos para a placa

## Configuração

1. Clone este repositório.
2. Copie `config.example.py` para `config.py`.
3. Preencha `api_key` e `wifi_password` em `config.py`.
4. Envie os arquivos do projeto para o ESP32, mantendo a pasta `frontend/`.
5. Execute ou reinicie a placa com `main.py`.
6. Abra no navegador o IP exibido no console serial, por exemplo `http://192.168.1.42`.

> `config.py` contém credenciais locais e já está no `.gitignore`. Não o envie ao GitHub.

## Estrutura

```text
.
├── frontend/
│   ├── index.html       # Interface do chat
│   ├── style.css        # Estilos responsivos
│   └── api.js           # Cliente HTTP e identificador do usuário
├── main.py              # Servidor HTTP e rotas da API
├── groq.py              # Cliente Groq e memória por usuário
├── wifi.py              # Conexão Wi-Fi
└── config.example.py    # Modelo de credenciais
```

## API

### `POST /api/chat`

```json
{
  "user_id": "id-unico-do-navegador",
  "prompt": "Olá!"
}
```

Resposta:

```json
{
  "response": "Olá! Como posso ajudar?"
}
```

### `POST /api/reset`

Remove apenas o histórico associado ao `user_id` enviado.

## Notas de capacidade

O ESP32 mantém as sessões em memória. Para preservar RAM, conversas antigas expiram automaticamente e apenas as últimas 12 mensagens de cada usuário são enviadas ao modelo. Reiniciar a placa também apaga os históricos.

## Segurança

Não exponha o ESP32 diretamente à internet. Use a aplicação apenas em uma rede confiável e mantenha sua chave da Groq somente no `config.py` local.
