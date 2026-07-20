from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM 提供商: "openai" | "ollama"
    llm_provider: str = "openai"

    # OpenAI / OpenAI 兼容接口（DeepSeek 等）
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o"

    # Ollama 本地模型
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # 浏览器
    browser_headless: bool = False
    # 浏览器渠道: "" (Playwright自带Chromium) | "msedge" (本机Edge) | "chrome" (本机Chrome)
    browser_channel: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
