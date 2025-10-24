"""
Workflow Engine for Travel Planner Multi-Agent System
Manages workflow execution and agent coordination
"""

from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime
import asyncio

class WorkflowEngine:
    """Manages workflow execution and agent coordination"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.workflows = {}
        self.active_workflows = {}
        self.workflow_history = []
        self.agent_registry = {}
    
    def register_workflow(self, name: str, workflow_config: Dict[str, Any]) -> bool:
        """Register a new workflow"""
        try:
            self.workflows[name] = {
                "config": workflow_config,
                "registered_at": datetime.now().isoformat(),
                "status": "registered"
            }
            self.logger.info(f"Workflow '{name}' registered successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error registering workflow '{name}': {str(e)}")
            return False
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> bool:
        """Register an agent for workflow execution"""
        try:
            self.agent_registry[agent_name] = {
                "instance": agent_instance,
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }
            self.logger.info(f"Agent '{agent_name}' registered successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error registering agent '{agent_name}': {str(e)}")
            return False
    
    def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a registered workflow"""
        try:
            if workflow_name not in self.workflows:
                return {"error": f"Workflow '{workflow_name}' not found"}
            
            workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_workflows[workflow_id] = {
                "workflow_name": workflow_name,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "input_data": input_data,
                "steps_completed": [],
                "current_step": None
            }
            
            workflow_config = self.workflows[workflow_name]["config"]
            result = self._execute_workflow_steps(workflow_id, workflow_config, input_data)
            
            # Update workflow status
            self.active_workflows[workflow_id]["status"] = "completed"
            self.active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
            self.active_workflows[workflow_id]["result"] = result
            
            # Add to history
            self.workflow_history.append({
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "status": "completed",
                "execution_time": self._calculate_execution_time(workflow_id),
                "result_summary": self._summarize_result(result)
            })
            
            self.logger.info(f"Workflow '{workflow_name}' completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow '{workflow_name}': {str(e)}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["error"] = str(e)
            return {"error": str(e)}
    
    def _execute_workflow_steps(self, workflow_id: str, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps sequentially"""
        steps = config.get("steps", [])
        current_data = input_data.copy()
        
        for step in steps:
            try:
                step_name = step.get("name", "unknown")
                step_type = step.get("type", "agent_call")
                
                self.active_workflows[workflow_id]["current_step"] = step_name
                
                if step_type == "agent_call":
                    result = self._execute_agent_step(step, current_data)
                elif step_type == "data_transform":
                    result = self._execute_transform_step(step, current_data)
                elif step_type == "condition":
                    result = self._execute_condition_step(step, current_data)
                else:
                    result = {"error": f"Unknown step type: {step_type}"}
                
                current_data.update(result)
                self.active_workflows[workflow_id]["steps_completed"].append(step_name)
                
            except Exception as e:
                self.logger.error(f"Error executing step '{step_name}': {str(e)}")
                current_data["error"] = str(e)
                break
        
        return current_data
    
    def _execute_agent_step(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent step"""
        agent_name = step.get("agent", "unknown")
        
        if agent_name not in self.agent_registry:
            return {"error": f"Agent '{agent_name}' not registered"}
        
        agent_instance = self.agent_registry[agent_name]["instance"]
        
        # Simulate agent execution
        result = {
            f"{agent_name}_result": f"Executed {agent_name} successfully",
            f"{agent_name}_timestamp": datetime.now().isoformat(),
            f"{agent_name}_status": "success"
        }
        
        return result
    
    def _execute_transform_step(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data transformation step"""
        transform_type = step.get("transform", "unknown")
        
        # Simulate data transformation
        result = {
            f"transform_{transform_type}": f"Applied {transform_type} transformation",
            f"transform_timestamp": datetime.now().isoformat(),
            f"transform_status": "success"
        }
        
        return result
    
    def _execute_condition_step(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conditional step"""
        condition = step.get("condition", "true")
        
        # Simulate condition evaluation
        result = {
            "condition_result": condition,
            "condition_timestamp": datetime.now().isoformat(),
            "condition_status": "evaluated"
        }
        
        return result
    
    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id:
            return self.active_workflows.get(workflow_id, {"error": "Workflow not found"})
        else:
            return {
                "registered_workflows": len(self.workflows),
                "active_workflows": len(self.active_workflows),
                "registered_agents": len(self.agent_registry),
                "workflow_history_count": len(self.workflow_history)
            }
    
    def _calculate_execution_time(self, workflow_id: str) -> float:
        """Calculate workflow execution time"""
        if workflow_id in self.active_workflows:
            started = datetime.fromisoformat(self.active_workflows[workflow_id]["started_at"])
            completed = datetime.fromisoformat(self.active_workflows[workflow_id]["completed_at"])
            return (completed - started).total_seconds()
        return 0.0
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize workflow result"""
        return {
            "success": "error" not in result,
            "data_keys": list(result.keys()),
            "result_size": len(str(result))
        }
    
    def stop_workflow(self, workflow_id: str) -> bool:
        """Stop a running workflow"""
        try:
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "stopped"
                self.active_workflows[workflow_id]["stopped_at"] = datetime.now().isoformat()
                self.logger.info(f"Workflow '{workflow_id}' stopped")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error stopping workflow '{workflow_id}': {str(e)}")
            return False
    
    def clear_workflow_history(self) -> None:
        """Clear workflow history"""
        self.workflow_history = []
        self.logger.info("Workflow history cleared")
    
    def export_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Export workflow configuration"""
        if workflow_name in self.workflows:
            return self.workflows[workflow_name]
        else:
            return {"error": f"Workflow '{workflow_name}' not found"}
