import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Import existing agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner import planner_agent
from agents.researcher import research_agent
from ml_models.recommendation_engine import RecommendationEngine
from ml_models.price_predictor import PricePredictor
from ml_models.sentiment_analyzer import SentimentAnalyzer
from ml_models.similarity_engine import SimilarityEngine
from data_collection.api_collector import APICollector
from data_collection.web_scraper import WebScraper
from data_collection.data_processor import DataProcessor
from visualization.analytics_engine import AnalyticsEngine

class AgentStatus(Enum):
    """Trạng thái của agent"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class AgentType(Enum):
    """Loại agent"""
    PLANNER = "planner"
    RESEARCHER = "researcher"
    RECOMMENDATION = "recommendation"
    PRICE_PREDICTOR = "price_predictor"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    SIMILARITY_ENGINE = "similarity_engine"
    API_COLLECTOR = "api_collector"
    WEB_SCRAPER = "web_scraper"
    DATA_PROCESSOR = "data_processor"
    ANALYTICS_ENGINE = "analytics_engine"

@dataclass
class AgentInfo:
    """Thông tin agent"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    status: AgentStatus
    created_at: datetime
    last_activity: datetime
    capabilities: List[str]
    dependencies: List[str]
    performance_metrics: Dict[str, Any]

@dataclass
class Task:
    """Task được giao cho agent"""
    task_id: str
    agent_id: str
    task_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    priority: int = 1

class AgentManager:
    def __init__(self):
        """Khởi tạo Agent Manager"""
        self.agents: Dict[str, Any] = {}
        self.agent_info: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.running = False
        self.logger = self._setup_logger()
        
        # Initialize agents
        self._initialize_agents()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger('AgentManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_agents(self):
        """Khởi tạo tất cả agents"""
        self.logger.info("Initializing agents...")
        
        # Initialize core agents
        self._register_agent(
            agent_type=AgentType.PLANNER,
            name="Travel Planner",
            description="Main planning agent for travel recommendations",
            agent_instance=planner_agent,
            capabilities=["planning", "recommendation", "coordination"],
            dependencies=[]
        )
        
        self._register_agent(
            agent_type=AgentType.RESEARCHER,
            name="Travel Researcher",
            description="Research agent for gathering travel information",
            agent_instance=research_agent,
            capabilities=["research", "data_gathering", "information_extraction"],
            dependencies=[]
        )
        
        # Initialize ML agents
        self._register_agent(
            agent_type=AgentType.RECOMMENDATION,
            name="Recommendation Engine",
            description="ML agent for generating recommendations",
            agent_instance=RecommendationEngine(),
            capabilities=["recommendation", "content_based_filtering", "collaborative_filtering"],
            dependencies=["data_processor"]
        )
        
        self._register_agent(
            agent_type=AgentType.PRICE_PREDICTOR,
            name="Price Predictor",
            description="ML agent for price prediction",
            agent_instance=PricePredictor(),
            capabilities=["price_prediction", "regression", "forecasting"],
            dependencies=["data_processor"]
        )
        
        self._register_agent(
            agent_type=AgentType.SENTIMENT_ANALYZER,
            name="Sentiment Analyzer",
            description="ML agent for sentiment analysis",
            agent_instance=SentimentAnalyzer(),
            capabilities=["sentiment_analysis", "text_processing", "nlp"],
            dependencies=["data_processor"]
        )
        
        self._register_agent(
            agent_type=AgentType.SIMILARITY_ENGINE,
            name="Similarity Engine",
            description="ML agent for similarity calculation",
            agent_instance=SimilarityEngine(),
            capabilities=["similarity_calculation", "clustering", "vector_operations"],
            dependencies=["data_processor"]
        )
        
        # Initialize data collection agents
        self._register_agent(
            agent_type=AgentType.API_COLLECTOR,
            name="API Collector",
            description="Agent for collecting data from APIs",
            agent_instance=APICollector(),
            capabilities=["api_integration", "data_collection", "rate_limiting"],
            dependencies=[]
        )
        
        self._register_agent(
            agent_type=AgentType.WEB_SCRAPER,
            name="Web Scraper",
            description="Agent for web scraping",
            agent_instance=WebScraper(),
            capabilities=["web_scraping", "data_extraction", "html_parsing"],
            dependencies=[]
        )
        
        self._register_agent(
            agent_type=AgentType.DATA_PROCESSOR,
            name="Data Processor",
            description="Agent for data processing and cleaning",
            agent_instance=DataProcessor(),
            capabilities=["data_processing", "data_cleaning", "data_transformation"],
            dependencies=["api_collector", "web_scraper"]
        )
        
        # Initialize analytics agent
        self._register_agent(
            agent_type=AgentType.ANALYTICS_ENGINE,
            name="Analytics Engine",
            description="Agent for data analytics and insights",
            agent_instance=AnalyticsEngine(),
            capabilities=["analytics", "statistics", "insights_generation"],
            dependencies=["data_processor"]
        )
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
    
    def _register_agent(self, agent_type: AgentType, name: str, description: str, 
                       agent_instance: Any, capabilities: List[str], dependencies: List[str]):
        """Đăng ký agent"""
        agent_id = str(uuid.uuid4())
        
        # Create agent info
        agent_info = AgentInfo(
            agent_id=agent_id,
            agent_type=agent_type,
            name=name,
            description=description,
            status=AgentStatus.IDLE,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            capabilities=capabilities,
            dependencies=dependencies,
            performance_metrics={
                'tasks_completed': 0,
                'tasks_failed': 0,
                'average_response_time': 0.0,
                'success_rate': 1.0
            }
        )
        
        # Store agent and info
        self.agents[agent_id] = agent_instance
        self.agent_info[agent_id] = agent_info
        
        self.logger.info(f"Registered agent: {name} ({agent_type.value})")
    
    def get_agent_by_type(self, agent_type: AgentType) -> Optional[Any]:
        """Lấy agent theo loại"""
        for agent_id, info in self.agent_info.items():
            if info.agent_type == agent_type:
                return self.agents[agent_id]
        return None
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Lấy thông tin agent"""
        return self.agent_info.get(agent_id)
    
    def get_all_agents_info(self) -> List[AgentInfo]:
        """Lấy thông tin tất cả agents"""
        return list(self.agent_info.values())
    
    def get_available_agents(self) -> List[AgentInfo]:
        """Lấy danh sách agents có sẵn"""
        return [info for info in self.agent_info.values() if info.status == AgentStatus.IDLE]
    
    def get_agents_by_capability(self, capability: str) -> List[AgentInfo]:
        """Lấy agents theo khả năng"""
        return [info for info in self.agent_info.values() if capability in info.capabilities]
    
    async def assign_task(self, agent_id: str, task_type: str, input_data: Dict[str, Any], 
                         priority: int = 1) -> str:
        """Giao task cho agent"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            input_data=input_data,
            output_data=None,
            status="pending",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            error_message=None,
            priority=priority
        )
        
        self.tasks[task_id] = task
        await self.task_queue.put(task)
        
        self.logger.info(f"Assigned task {task_id} to agent {agent_id}")
        return task_id
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Thực thi task"""
        agent_id = task.agent_id
        agent = self.agents.get(agent_id)
        agent_info = self.agent_info.get(agent_id)
        
        if not agent or not agent_info:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Update agent status
        agent_info.status = AgentStatus.BUSY
        agent_info.last_activity = datetime.now()
        task.started_at = datetime.now()
        task.status = "running"
        
        try:
            # Execute task based on type
            result = await self._execute_task_by_type(agent, task)
            
            # Update task status
            task.status = "completed"
            task.completed_at = datetime.now()
            task.output_data = result
            
            # Update agent metrics
            agent_info.performance_metrics['tasks_completed'] += 1
            agent_info.status = AgentStatus.IDLE
            
            self.logger.info(f"Task {task.task_id} completed successfully")
            return result
            
        except Exception as e:
            # Handle error
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            agent_info.performance_metrics['tasks_failed'] += 1
            agent_info.status = AgentStatus.ERROR
            
            self.logger.error(f"Task {task.task_id} failed: {e}")
            raise e
    
    async def _execute_task_by_type(self, agent: Any, task: Task) -> Dict[str, Any]:
        """Thực thi task theo loại"""
        task_type = task.task_type
        input_data = task.input_data
        
        if task_type == "recommendation":
            if hasattr(agent, 'get_content_based_recommendations'):
                return agent.get_content_based_recommendations(
                    input_data.get('user_preferences', {}),
                    input_data.get('places_data', []),
                    input_data.get('top_k', 10)
                )
        
        elif task_type == "price_prediction":
            if hasattr(agent, 'predict_hotel_price'):
                return agent.predict_hotel_price(input_data.get('hotel_data', {}))
        
        elif task_type == "sentiment_analysis":
            if hasattr(agent, 'analyze_sentiment'):
                return agent.analyze_sentiment(input_data.get('text', ''))
        
        elif task_type == "similarity_calculation":
            if hasattr(agent, 'calculate_overall_similarity'):
                return agent.calculate_overall_similarity(
                    input_data.get('place1', {}),
                    input_data.get('place2', {})
                )
        
        elif task_type == "data_collection":
            if hasattr(agent, 'collect_places_data'):
                return agent.collect_places_data(input_data.get('city', ''))
        
        elif task_type == "web_scraping":
            if hasattr(agent, 'scrape_places'):
                return agent.scrape_places(input_data.get('city', ''))
        
        elif task_type == "data_processing":
            if hasattr(agent, 'process_places_data'):
                return agent.process_places_data(input_data.get('raw_data', []))
        
        elif task_type == "analytics":
            if hasattr(agent, 'get_comprehensive_analysis'):
                return agent.get_comprehensive_analysis(input_data.get('places_data', []))
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def start_task_processor(self):
        """Bắt đầu xử lý tasks"""
        self.running = True
        self.logger.info("Starting task processor...")
        
        while self.running:
            try:
                # Get task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute task
                await self.execute_task(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing task: {e}")
    
    def stop_task_processor(self):
        """Dừng xử lý tasks"""
        self.running = False
        self.logger.info("Stopping task processor...")
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Lấy trạng thái task"""
        return self.tasks.get(task_id)
    
    def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Lấy performance của agent"""
        agent_info = self.agent_info.get(agent_id)
        if agent_info:
            return agent_info.performance_metrics
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hệ thống"""
        total_agents = len(self.agents)
        idle_agents = len([info for info in self.agent_info.values() if info.status == AgentStatus.IDLE])
        busy_agents = len([info for info in self.agent_info.values() if info.status == AgentStatus.BUSY])
        error_agents = len([info for info in self.agent_info.values() if info.status == AgentStatus.ERROR])
        
        total_tasks = len(self.tasks)
        completed_tasks = len([task for task in self.tasks.values() if task.status == "completed"])
        failed_tasks = len([task for task in self.tasks.values() if task.status == "failed"])
        pending_tasks = len([task for task in self.tasks.values() if task.status == "pending"])
        
        return {
            'agents': {
                'total': total_agents,
                'idle': idle_agents,
                'busy': busy_agents,
                'error': error_agents
            },
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'pending': pending_tasks
            },
            'system_health': 'healthy' if error_agents == 0 else 'degraded'
        }
    
    def reset_agent(self, agent_id: str):
        """Reset agent về trạng thái ban đầu"""
        agent_info = self.agent_info.get(agent_id)
        if agent_info:
            agent_info.status = AgentStatus.IDLE
            agent_info.last_activity = datetime.now()
            self.logger.info(f"Reset agent {agent_id}")
    
    def get_agent_dependencies(self, agent_id: str) -> List[str]:
        """Lấy dependencies của agent"""
        agent_info = self.agent_info.get(agent_id)
        if agent_info:
            return agent_info.dependencies
        return []
    
    def check_dependencies(self, agent_id: str) -> bool:
        """Kiểm tra dependencies của agent"""
        dependencies = self.get_agent_dependencies(agent_id)
        for dep in dependencies:
            # Check if dependency agent is available
            dep_agents = self.get_agents_by_capability(dep)
            if not dep_agents:
                return False
        return True
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Lấy capabilities của agent"""
        agent_info = self.agent_info.get(agent_id)
        if agent_info:
            return agent_info.capabilities
        return []
    
    def find_best_agent_for_task(self, task_type: str, required_capabilities: List[str] = None) -> Optional[str]:
        """Tìm agent tốt nhất cho task"""
        available_agents = self.get_available_agents()
        
        if not available_agents:
            return None
        
        # Filter by capabilities if specified
        if required_capabilities:
            capable_agents = []
            for agent_info in available_agents:
                if all(cap in agent_info.capabilities for cap in required_capabilities):
                    capable_agents.append(agent_info)
            available_agents = capable_agents
        
        if not available_agents:
            return None
        
        # Find agent with best performance
        best_agent = max(available_agents, key=lambda x: x.performance_metrics['success_rate'])
        return best_agent.agent_id
    
    def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Cập nhật metrics của agent"""
        agent_info = self.agent_info.get(agent_id)
        if agent_info:
            agent_info.performance_metrics.update(metrics)
            self.logger.info(f"Updated metrics for agent {agent_id}")
    
    def export_agent_info(self) -> Dict[str, Any]:
        """Export thông tin agents"""
        return {
            'agents': {agent_id: asdict(info) for agent_id, info in self.agent_info.items()},
            'tasks': {task_id: asdict(task) for task_id, task in self.tasks.items()},
            'system_status': self.get_system_status(),
            'exported_at': datetime.now().isoformat()
        }
