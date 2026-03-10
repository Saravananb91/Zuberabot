"""Configuration schema using Pydantic."""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class WhatsAppConfig(BaseModel):
    """WhatsApp channel configuration."""
    enabled: bool = False
    bridge_url: str = "ws://localhost:3001"
    allow_from: list[str] = Field(default_factory=list)  # Allowed phone numbers


class ChannelsConfig(BaseModel):
    """Configuration for WhatsApp channel."""
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)


class AgentDefaults(BaseModel):
    """Default agent configuration."""
    workspace: str = "~/.zuberabot/workspace"
    model: str = "ollama/qwen2.5:3b"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 20


class AgentsConfig(BaseModel):
    """Agent configuration."""
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class ProviderConfig(BaseModel):
    """LLM provider configuration."""
    api_key: str = ""
    api_base: str | None = None


class ProvidersConfig(BaseModel):
    """Configuration for LLM providers."""
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    ollama: ProviderConfig = Field(default_factory=ProviderConfig)


class GatewayConfig(BaseModel):
    """Gateway/server configuration."""
    host: str = "0.0.0.0"
    port: int = 18790


class WebSearchConfig(BaseModel):
    """Web search tool configuration."""
    api_key: str = ""  # Brave Search API key
    max_results: int = 5


class WebToolsConfig(BaseModel):
    """Web tools configuration."""
    enabled: bool = True
    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ToolsConfig(BaseModel):
    """Tools configuration."""
    web: WebToolsConfig = Field(default_factory=WebToolsConfig)


class Config(BaseSettings):
    """Root configuration for zuberabot."""
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    @property
    def workspace_path(self) -> Path:
        """Get expanded workspace path."""
        return Path(self.agents.defaults.workspace).expanduser()

    def get_api_key(self) -> str | None:
        """Get API key based on configured model or in priority order."""
        model = self.agents.defaults.model

        if model.startswith("ollama/"):
            return None
        if model.startswith("groq/"):
            return self.providers.groq.api_key or None
        if model.startswith("openrouter/"):
            return self.providers.openrouter.api_key or None
        if model.startswith("gemini/"):
            return self.providers.gemini.api_key or None
        if model.startswith("anthropic/"):
            return self.providers.anthropic.api_key or None

        # Priority order fallback
        return (
            self.providers.openrouter.api_key or
            self.providers.anthropic.api_key or
            self.providers.openai.api_key or
            self.providers.gemini.api_key or
            self.providers.zhipu.api_key or
            self.providers.groq.api_key or
            None
        )

    def get_api_base(self) -> str | None:
        """Get API base URL based on configured model."""
        model = self.agents.defaults.model

        if model.startswith("ollama/"):
            return self.providers.ollama.api_base or "http://localhost:11434"
        if model.startswith("openrouter/"):
            return self.providers.openrouter.api_base or "https://openrouter.ai/api/v1"
        if self.providers.zhipu.api_key:
            return self.providers.zhipu.api_base
        return None

    class Config:
        env_prefix = "NANOBOT_"
        env_nested_delimiter = "__"
