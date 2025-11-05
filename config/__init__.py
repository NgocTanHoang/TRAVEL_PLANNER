"""
Centralized LangSmith Configuration
====================================
Quản lý tập trung cấu hình LangSmith cho toàn bộ hệ thống.
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file từ project root
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / '.env'
if _env_path.exists():
    load_dotenv(_env_path, encoding='utf-8')


class LangSmithConfig:
    """Centralized LangSmith configuration"""
    
    # Default values
    DEFAULT_TRACING_ENABLED = True
    DEFAULT_PROJECT_NAME = 'vi-vu-travel-planner'
    DEFAULT_ENDPOINT = 'https://api.smith.langchain.com'
    
    def __init__(self):
        """Initialize LangSmith configuration"""
        self._setup_environment()
    
    def _setup_environment(self):
        """Setup environment variables for LangSmith"""
        # Tracing enabled/disabled
        tracing_v2 = os.getenv('LANGCHAIN_TRACING_V2', str(self.DEFAULT_TRACING_ENABLED).lower())
        os.environ['LANGCHAIN_TRACING_V2'] = tracing_v2
        
        # API Key
        api_key = os.getenv('LANGCHAIN_API_KEY', '')
        if api_key:
            os.environ['LANGCHAIN_API_KEY'] = api_key
        
        # Project name
        project = os.getenv('LANGCHAIN_PROJECT', self.DEFAULT_PROJECT_NAME)
        os.environ['LANGCHAIN_PROJECT'] = project
        
        # Endpoint (optional, defaults to LangSmith cloud)
        endpoint = os.getenv('LANGCHAIN_ENDPOINT', self.DEFAULT_ENDPOINT)
        if endpoint:
            os.environ['LANGCHAIN_ENDPOINT'] = endpoint
        
        # Tags (optional)
        tags = os.getenv('LANGCHAIN_TAGS', '')
        if tags:
            os.environ['LANGCHAIN_TAGS'] = tags
    
    @property
    def tracing_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled"""
        return os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    
    @property
    def api_key(self) -> Optional[str]:
        """Get LangSmith API key"""
        return os.getenv('LANGCHAIN_API_KEY', '')
    
    @property
    def project_name(self) -> str:
        """Get LangSmith project name"""
        return os.getenv('LANGCHAIN_PROJECT', self.DEFAULT_PROJECT_NAME)
    
    @property
    def endpoint(self) -> str:
        """Get LangSmith endpoint"""
        return os.getenv('LANGCHAIN_ENDPOINT', self.DEFAULT_ENDPOINT)
    
    def get_runnable_config(self, tags: Optional[list] = None, metadata: Optional[dict] = None):
        """
        Get LangChain RunnableConfig for tracing.
        
        Args:
            tags: Additional tags for this run
            metadata: Additional metadata
            
        Returns:
            RunnableConfig dict
        """
        from langchain_core.runnables import RunnableConfig
        from datetime import datetime
        
        config_tags = ['travel-planner', self.project_name]
        if tags:
            config_tags.extend(tags)
        
        config_metadata = {
            'project': self.project_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            config_metadata.update(metadata)
        
        return RunnableConfig(
            tags=config_tags,
            metadata=config_metadata
        )
    
    def is_configured(self) -> bool:
        """Check if LangSmith is properly configured"""
        return bool(self.api_key) and self.tracing_enabled


# Singleton instance
_config_instance: Optional[LangSmithConfig] = None


def get_langsmith_config() -> LangSmithConfig:
    """Get or create LangSmith config singleton"""
    global _config_instance
    if _config_instance is None:
        _config_instance = LangSmithConfig()
    return _config_instance


# Initialize on import
_langsmith_config = get_langsmith_config()

