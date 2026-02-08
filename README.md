# Tel-Anti: Stateful Telegram MCP Server

Tel-Anti는 Antigravity 에이전트와 사용자를 텔레그램을 통해 유기적으로 연결해주는 고도화된 MCP(Model Context Protocol) 서버입니다.

## 🌟 주요 특징

- **Stateful Management**: `tg_state.json`을 통해 마지막 메시지 ID를 보관하므로, 시스템 재시작 시에도 메시지 유실이 없습니다.
- **Pulsing Long-Polling**: IDE 타임아웃을 방지하면서도 실시간에 가까운 대기(Wait-Notify) 상태를 유지합니다.
- **Direct API Interaction**: 프록시 이슈를 우회하여 텔레그램 API와 직접 통신하므로 응답 속도가 빠르고 안정적입니다.

## 🚀 시작하기

### 1. 전제 조건
- Python 3.10 이상
- Telegram Bot Token 및 Chat ID

### 2. 설치
```bash
git clone https://github.com/kankinku/Antigravity-SNS-Connector.git
cd tel-anti
pip install -r requirements.txt
```

### 3. 설정 (mcp_config.json) - **가장 중요한 단계**

MCP 서버는 `mcp_config.json`의 `env` 설정을 통해 토큰을 전달받습니다. 아래 방법 중 하나를 선택하세요.

#### 방법 A: uvx를 이용한 GitHub 직접 실행 (권장)
로컬에 복제할 필요 없이 GitHub에서 직접 실행합니다. `uv`가 설치되어 있어야 합니다.
```json
{
  "mcpServers": {
    "tel-anti": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/kankinku/Antigravity-SNS-Connector.git",
        "tel-anti"
      ],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token_here",
        "TELEGRAM_CHAT_ID": "your_chat_id_here"
      }
    }
  }
}
```

#### 방법 B: 로컬 파이썬 실행
```json
{
  "mcpServers": {
    "tel-anti": {
      "command": "python",
      "args": ["/absolute/path/to/tel-anti/src/tel_anti/telegram_mcp_server.py"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your_token_here",
        "TELEGRAM_CHAT_ID": "your_chat_id_here"
      }
    }
  }
}
```

---

### 4. (선택 사항) 로컬 개발 및 단독 실행
MCP 없이 스크립트를 직접 실행(`python telegram_mcp_server.py`)하고 싶을 때만 `.env` 파일이 필요합니다.
1. `.env.example` -> `.env`로 복사
2. `.env` 파일에 토큰 정보 입력

## 📚 문서
- [아키텍처 설계](./docs/architecture.md)
- [버전 비교 분석](./docs/comparison.md)

## ⚖️ 라이선스
MIT License
