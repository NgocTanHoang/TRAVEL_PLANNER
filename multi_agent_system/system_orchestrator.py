import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import time

# Import existing components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .agent_manager import AgentManager, AgentType, AgentStatus

class SystemStatus(Enum):
    """Trạng thái hệ thống"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class SystemMode(Enum):
    """Chế độ hệ thống"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"

@dataclass
class SystemConfig:
    """Cấu hình hệ thống"""
    system_id: str
    name: str
    description: str
    mode: SystemMode
    max_concurrent_workflows: int = 5
    max_concurrent_pipelines: int = 3
    heartbeat_interval: int = 30  # seconds
    health_check_interval: int = 60  # seconds
    log_level: str = "INFO"
    enable_monitoring: bool = True
    enable_metrics: bool = True

@dataclass
class SystemMetrics:
    """Metrics của hệ thống"""
    uptime: float
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    total_pipelines: int
    active_pipelines: int
    completed_pipelines: int
    failed_pipelines: int
    total_agents: int
    active_agents: int
    idle_agents: int
    error_agents: int
    total_messages: int
    messages_per_second: float
    system_load: float
    memory_usage: float
    cpu_usage: float

class SystemOrchestrator:
    def __init__(self, config: SystemConfig):
        """Khởi tạo System Orchestrator"""
        self.config = config
        self.status = SystemStatus.INITIALIZING
        self.start_time = datetime.now()
        self.logger = self._setup_logger()
        
        # Initialize components
        self.agent_manager = AgentManager()
        
        # System monitoring
        self.metrics = SystemMetrics(
            uptime=0.0,
            total_workflows=0,
            active_workflows=0,
            completed_workflows=0,
            failed_workflows=0,
            total_pipelines=0,
            active_pipelines=0,
            completed_pipelines=0,
            failed_pipelines=0,
            total_agents=0,
            active_agents=0,
            idle_agents=0,
            error_agents=0,
            total_messages=0,
            messages_per_second=0.0,
            system_load=0.0,
            memory_usage=0.0,
            cpu_usage=0.0
        )
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.running = False
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # System health
        self.health_status = {
            'overall': 'healthy',
            'components': {
                'agent_manager': 'healthy',
            },
            'last_check': datetime.now()
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(f'SystemOrchestrator_{self.config.system_id}')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start_system(self):
        """Khởi động hệ thống"""
        self.logger.info("Starting Multi-Agent Data Science System...")
        
        try:
            # Start agent manager
            await self._start_agent_manager()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Update system status
            self.status = SystemStatus.RUNNING
            self.running = True
            
            self.logger.info("System started successfully")
            
            # Emit system started event
            await self._emit_event('system_started', {'timestamp': datetime.now().isoformat()})
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"Failed to start system: {e}")
            raise e
    
    async def stop_system(self):
        """Dừng hệ thống"""
        self.logger.info("Stopping Multi-Agent Data Science System...")
        
        try:
            # Update system status
            self.status = SystemStatus.STOPPING
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Stop agent manager
            await self._stop_agent_manager()
            
            # Update system status
            self.status = SystemStatus.STOPPED
            self.running = False
            
            self.logger.info("System stopped successfully")
            
            # Emit system stopped event
            await self._emit_event('system_stopped', {'timestamp': datetime.now().isoformat()})
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"Error stopping system: {e}")
            raise e
    
    async def _start_agent_manager(self):
        """Khởi động agent manager"""
        self.logger.info("Starting agent manager...")
        
        # Start task processor
        task = asyncio.create_task(self.agent_manager.start_task_processor())
        self.background_tasks.append(task)
        
        self.logger.info("Agent manager started")
    
    async def _start_background_tasks(self):
        """Khởi động background tasks"""
        self.logger.info("Starting background tasks...")
        
        # Health check task
        health_check_task = asyncio.create_task(self._health_check_loop())
        self.background_tasks.append(health_check_task)
        
        # Metrics collection task
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self.background_tasks.append(metrics_task)
        
        self.logger.info("Background tasks started")
    
    async def _stop_background_tasks(self):
        """Dừng background tasks"""
        self.logger.info("Stopping background tasks...")
        
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        self.logger.info("Background tasks stopped")
    
    async def _stop_agent_manager(self):
        """Dừng agent manager"""
        self.logger.info("Stopping agent manager...")
        
        self.agent_manager.stop_task_processor()
        
        self.logger.info("Agent manager stopped")
    
    async def _health_check_loop(self):
        """Health check loop"""
        while self.running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_collection_loop(self):
        """Metrics collection loop"""
        while self.running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_check(self):
        """Thực hiện health check"""
        health_status = {
            'overall': 'healthy',
            'components': {},
            'last_check': datetime.now()
        }
        
        # Check agent manager
        try:
            agent_status = self.agent_manager.get_system_status()
            health_status['components']['agent_manager'] = 'healthy'
        except Exception as e:
            health_status['components']['agent_manager'] = 'unhealthy'
            self.logger.error(f"Agent manager health check failed: {e}")
        
        # Determine overall health
        unhealthy_components = [comp for comp, status in health_status['components'].items() if status == 'unhealthy']
        if unhealthy_components:
            health_status['overall'] = 'unhealthy'
        
        self.health_status = health_status
        
        # Emit health check event
        await self._emit_event('health_check', health_status)
    
    async def _collect_metrics(self):
        """Thu thập metrics"""
        current_time = datetime.now()
        uptime = (current_time - self.start_time).total_seconds()
        
        # Get agent metrics
        agent_status = self.agent_manager.get_system_status()
        
        # Update system metrics
        self.metrics.uptime = uptime
        self.metrics.total_agents = agent_status.get('agents', {}).get('total', 0)
        self.metrics.active_agents = agent_status.get('agents', {}).get('busy', 0)
        self.metrics.idle_agents = agent_status.get('agents', {}).get('idle', 0)
        self.metrics.error_agents = agent_status.get('agents', {}).get('error', 0)
        
        # Emit metrics event
        await self._emit_event('metrics_updated', asdict(self.metrics))
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event_type, data)
                except Exception as e:
                    self.logger.error(f"Error in event handler: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Đăng ký event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Hủy đăng ký event handler"""
        if event_type in self.event_handlers:
            if handler in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hệ thống"""
        return {
            'system_id': self.config.system_id,
            'name': self.config.name,
            'status': self.status.value,
            'mode': self.config.mode.value,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'health': self.health_status,
            'metrics': asdict(self.metrics),
            'components': {
                'agent_manager': self.agent_manager.get_system_status(),
            }
        }
    
    def get_system_metrics(self) -> SystemMetrics:
        """Lấy metrics của hệ thống"""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Lấy trạng thái sức khỏe hệ thống"""
        return self.health_status
    
    def pause_system(self):
        """Tạm dừng hệ thống"""
        if self.status == SystemStatus.RUNNING:
            self.status = SystemStatus.PAUSED
            self.logger.info("System paused")
    
    def resume_system(self):
        """Tiếp tục hệ thống"""
        if self.status == SystemStatus.PAUSED:
            self.status = SystemStatus.RUNNING
            self.logger.info("System resumed")
    
    def export_system_data(self) -> Dict[str, Any]:
        """Export dữ liệu hệ thống"""
        return {
            'config': asdict(self.config),
            'status': self.status.value,
            'health': self.health_status,
            'metrics': asdict(self.metrics),
            'agent_manager': self.agent_manager.export_agent_info(),
            'exported_at': datetime.now().isoformat()
        }
