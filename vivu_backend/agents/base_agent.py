"""
Base Agent class for all Vi Vu agents.
Provides common functionality: logging, LangSmith tracing, error handling.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import centralized LangSmith config
from config.langsmith_config import get_langsmith_config

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all AI agents in the Vi Vu system.
    
    Features:
    - LangSmith tracing integration
    - Structured logging
    - Error handling with retries
    - Performance monitoring
    """
    
    def __init__(self, agent_name: str, description: str = ""):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for this agent
            description: Human-readable description of agent's purpose
        """
        self.agent_name = agent_name
        self.description = description
        self.logger = logging.getLogger(f"agents.{agent_name}")
        
        # Use centralized LangSmith configuration
        self.langsmith_config = get_langsmith_config()
        
        self.logger.info(f"Initialized agent: {agent_name}")
        if self.langsmith_config.tracing_enabled:
            self.logger.info(f"LangSmith tracing enabled for {agent_name}")
    
    def get_runnable_config(self, tags: Optional[list] = None, metadata: Optional[dict] = None):
        """
        Get LangChain runnable config for tracing.
        
        Args:
            tags: Additional tags for this run
            metadata: Additional metadata
            
        Returns:
            RunnableConfig with tracing enabled
        """
        config_tags = [self.agent_name, 'travel-planner']
        if tags:
            config_tags.extend(tags)
        
        config_metadata = {
            'agent': self.agent_name,
            'description': self.description
        }
        if metadata:
            config_metadata.update(metadata)
        
        return self.langsmith_config.get_runnable_config(
            tags=config_tags,
            metadata=config_metadata
        )
    
    def log_input(self, input_data: Dict[str, Any]) -> None:
        """Log agent input."""
        self.logger.info(f"[{self.agent_name}] Input: {self._sanitize_for_log(input_data)}")
    
    def log_output(self, output_data: Dict[str, Any]) -> None:
        """Log agent output."""
        self.logger.info(f"[{self.agent_name}] Output: {self._sanitize_for_log(output_data)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log agent errors."""
        self.logger.error(
            f"[{self.agent_name}] Error: {str(error)}",
            extra={'context': context or {}},
            exc_info=True
        )
    
    def _sanitize_for_log(self, data: Dict[str, Any], max_length: int = 200) -> str:
        """
        Sanitize data for logging (truncate long strings).
        
        Args:
            data: Data to sanitize
            max_length: Maximum string length
            
        Returns:
            Sanitized string representation
        """
        data_str = str(data)
        if len(data_str) > max_length:
            return data_str[:max_length] + '...'
        return data_str
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        This method should be overridden by subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state after agent execution
        """
        raise NotImplementedError(f"{self.agent_name} must implement execute()")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.agent_name}')>"

