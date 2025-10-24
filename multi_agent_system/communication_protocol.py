"""
Communication Protocol for Travel Planner Multi-Agent System
Handles inter-agent communication and message routing
"""

from typing import Dict, List, Any, Optional, Callable
import logging
from datetime import datetime
import json
import uuid

class CommunicationProtocol:
    """Handles inter-agent communication and message routing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.message_queue = []
        self.agent_subscriptions = {}
        self.message_history = []
        self.routing_rules = {}
        self.message_handlers = {}
    
    def register_agent(self, agent_name: str, message_handler: Callable = None) -> bool:
        """Register an agent for communication"""
        try:
            self.agent_subscriptions[agent_name] = {
                "registered_at": datetime.now().isoformat(),
                "status": "active",
                "message_handler": message_handler,
                "message_count": 0
            }
            self.logger.info(f"Agent '{agent_name}' registered for communication")
            return True
        except Exception as e:
            self.logger.error(f"Error registering agent '{agent_name}': {str(e)}")
            return False
    
    def send_message(self, sender: str, recipient: str, message_type: str, 
                    content: Dict[str, Any], priority: str = "normal") -> str:
        """Send a message between agents"""
        try:
            message_id = str(uuid.uuid4())
            message = {
                "id": message_id,
                "sender": sender,
                "recipient": recipient,
                "type": message_type,
                "content": content,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "status": "sent"
            }
            
            self.message_queue.append(message)
            self.message_history.append(message)
            
            # Update agent message count
            if recipient in self.agent_subscriptions:
                self.agent_subscriptions[recipient]["message_count"] += 1
            
            self.logger.info(f"Message sent from '{sender}' to '{recipient}': {message_type}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return None
    
    def broadcast_message(self, sender: str, message_type: str, 
                         content: Dict[str, Any], exclude: List[str] = None) -> List[str]:
        """Broadcast a message to all registered agents"""
        try:
            exclude = exclude or []
            message_ids = []
            
            for agent_name in self.agent_subscriptions:
                if agent_name != sender and agent_name not in exclude:
                    message_id = self.send_message(sender, agent_name, message_type, content)
                    if message_id:
                        message_ids.append(message_id)
            
            self.logger.info(f"Message broadcasted to {len(message_ids)} agents")
            return message_ids
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {str(e)}")
            return []
    
    def process_messages(self, agent_name: str) -> List[Dict[str, Any]]:
        """Process messages for a specific agent"""
        try:
            if agent_name not in self.agent_subscriptions:
                return []
            
            # Get messages for this agent
            agent_messages = [
                msg for msg in self.message_queue 
                if msg["recipient"] == agent_name and msg["status"] == "sent"
            ]
            
            # Process messages
            processed_messages = []
            for message in agent_messages:
                try:
                    # Update message status
                    message["status"] = "processed"
                    message["processed_at"] = datetime.now().isoformat()
                    
                    # Call message handler if available
                    handler = self.agent_subscriptions[agent_name]["message_handler"]
                    if handler:
                        handler(message)
                    
                    processed_messages.append(message)
                    
                except Exception as e:
                    message["status"] = "error"
                    message["error"] = str(e)
                    self.logger.error(f"Error processing message {message['id']}: {str(e)}")
            
            self.logger.info(f"Processed {len(processed_messages)} messages for '{agent_name}'")
            return processed_messages
            
        except Exception as e:
            self.logger.error(f"Error processing messages for '{agent_name}': {str(e)}")
            return []
    
    def add_routing_rule(self, rule_name: str, condition: Callable, 
                        action: Callable) -> bool:
        """Add a routing rule for message handling"""
        try:
            self.routing_rules[rule_name] = {
                "condition": condition,
                "action": action,
                "created_at": datetime.now().isoformat()
            }
            self.logger.info(f"Routing rule '{rule_name}' added")
            return True
        except Exception as e:
            self.logger.error(f"Error adding routing rule '{rule_name}': {str(e)}")
            return False
    
    def apply_routing_rules(self, message: Dict[str, Any]) -> bool:
        """Apply routing rules to a message"""
        try:
            for rule_name, rule in self.routing_rules.items():
                if rule["condition"](message):
                    rule["action"](message)
                    self.logger.info(f"Applied routing rule '{rule_name}' to message {message['id']}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error applying routing rules: {str(e)}")
            return False
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get status of a specific message"""
        for message in self.message_history:
            if message["id"] == message_id:
                return {
                    "id": message["id"],
                    "status": message["status"],
                    "timestamp": message["timestamp"],
                    "processed_at": message.get("processed_at"),
                    "error": message.get("error")
                }
        return {"error": "Message not found"}
    
    def get_agent_communication_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get communication statistics for an agent"""
        if agent_name not in self.agent_subscriptions:
            return {"error": "Agent not found"}
        
        sent_messages = len([msg for msg in self.message_history if msg["sender"] == agent_name])
        received_messages = len([msg for msg in self.message_history if msg["recipient"] == agent_name])
        
        return {
            "agent_name": agent_name,
            "sent_messages": sent_messages,
            "received_messages": received_messages,
            "registered_at": self.agent_subscriptions[agent_name]["registered_at"],
            "status": self.agent_subscriptions[agent_name]["status"]
        }
    
    def get_system_communication_stats(self) -> Dict[str, Any]:
        """Get overall communication statistics"""
        total_messages = len(self.message_history)
        active_agents = len([agent for agent in self.agent_subscriptions.values() if agent["status"] == "active"])
        
        message_types = {}
        for message in self.message_history:
            msg_type = message["type"]
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        return {
            "total_messages": total_messages,
            "active_agents": active_agents,
            "message_types": message_types,
            "routing_rules": len(self.routing_rules),
            "queue_size": len(self.message_queue)
        }
    
    def clear_message_queue(self) -> None:
        """Clear the message queue"""
        self.message_queue = []
        self.logger.info("Message queue cleared")
    
    def clear_message_history(self) -> None:
        """Clear message history"""
        self.message_history = []
        self.logger.info("Message history cleared")
    
    def export_communication_log(self, format: str = "json") -> str:
        """Export communication log"""
        try:
            log_data = {
                "exported_at": datetime.now().isoformat(),
                "message_history": self.message_history,
                "agent_subscriptions": self.agent_subscriptions,
                "routing_rules": list(self.routing_rules.keys())
            }
            
            if format == "json":
                return json.dumps(log_data, indent=2)
            else:
                return str(log_data)
                
        except Exception as e:
            self.logger.error(f"Error exporting communication log: {str(e)}")
            return f"Error: {str(e)}"
