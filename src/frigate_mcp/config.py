"""
Configuration management for Frigate MCP server.

Handles environment variables and settings validation.
"""

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class FrigateConfig(BaseSettings):
    """
    Configuration settings for connecting to Frigate.
    
    Attributes:
        frigate_url: Base URL of the Frigate instance (e.g., http://localhost:5000)
        api_key: Optional API key for authentication (if Frigate requires it)
        timeout: HTTP request timeout in seconds
        server_host: Host to bind the HTTP/SSE server to
        server_port: Port to bind the HTTP/SSE server to
    """
    
    model_config = SettingsConfigDict(
        env_prefix="FRIGATE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    frigate_url: HttpUrl = Field(
        default="http://localhost:5000",
        description="Base URL of the Frigate instance"
    )
    
    api_key: str | None = Field(
        default=None,
        description="Optional API key for Frigate authentication"
    )
    
    timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        ge=1,
        le=300
    )
    
    server_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the HTTP/SSE server to"
    )
    
    server_port: int = Field(
        default=8000,
        description="Port to bind the HTTP/SSE server to",
        ge=1,
        le=65535
    )
    
    @property
    def base_url(self) -> str:
        """Return the base URL as a string."""
        return str(self.frigate_url).rstrip("/")
    
    @property
    def api_base_url(self) -> str:
        """Return the API base URL."""
        return f"{self.base_url}/api"
