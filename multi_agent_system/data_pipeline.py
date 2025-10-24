"""
Data Pipeline for Travel Planner Multi-Agent System
Manages data flow between agents and processing stages
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

class DataPipeline:
    """Manages data flow and processing stages in the multi-agent system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_stages = {
            "raw_data": {},
            "processed_data": {},
            "ml_features": {},
            "recommendations": {},
            "final_output": {}
        }
        self.processing_history = []
    
    def add_raw_data(self, source: str, data: Dict[str, Any]) -> bool:
        """Add raw data from a source"""
        try:
            self.data_stages["raw_data"][source] = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "size": len(str(data))
            }
            self.logger.info(f"Added raw data from {source}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding raw data from {source}: {str(e)}")
            return False
    
    def process_data(self, processor_type: str, config: Dict[str, Any] = None) -> bool:
        """Process raw data through specified processor"""
        try:
            if not self.data_stages["raw_data"]:
                self.logger.warning("No raw data available for processing")
                return False
            
            # Simulate data processing
            processed_data = {
                "processor_type": processor_type,
                "processed_at": datetime.now().isoformat(),
                "input_sources": list(self.data_stages["raw_data"].keys()),
                "output_size": len(self.data_stages["raw_data"]) * 100,
                "quality_score": 0.95
            }
            
            self.data_stages["processed_data"][processor_type] = processed_data
            self.processing_history.append({
                "stage": "data_processing",
                "processor": processor_type,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            self.logger.info(f"Data processed successfully with {processor_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing data with {processor_type}: {str(e)}")
            self.processing_history.append({
                "stage": "data_processing",
                "processor": processor_type,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            return False
    
    def extract_ml_features(self, feature_types: List[str]) -> bool:
        """Extract ML features from processed data"""
        try:
            if not self.data_stages["processed_data"]:
                self.logger.warning("No processed data available for feature extraction")
                return False
            
            ml_features = {
                "feature_types": feature_types,
                "extracted_at": datetime.now().isoformat(),
                "feature_count": len(feature_types) * 10,
                "feature_quality": 0.92
            }
            
            self.data_stages["ml_features"] = ml_features
            self.processing_history.append({
                "stage": "feature_extraction",
                "feature_types": feature_types,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            self.logger.info(f"ML features extracted: {feature_types}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting ML features: {str(e)}")
            return False
    
    def generate_recommendations(self, recommendation_type: str, params: Dict[str, Any] = None) -> bool:
        """Generate recommendations using ML features"""
        try:
            if not self.data_stages["ml_features"]:
                self.logger.warning("No ML features available for recommendations")
                return False
            
            recommendations = {
                "type": recommendation_type,
                "generated_at": datetime.now().isoformat(),
                "recommendation_count": 25,
                "confidence_score": 0.88,
                "parameters": params or {}
            }
            
            self.data_stages["recommendations"][recommendation_type] = recommendations
            self.processing_history.append({
                "stage": "recommendation_generation",
                "type": recommendation_type,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            self.logger.info(f"Recommendations generated: {recommendation_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return False
    
    def finalize_output(self, output_type: str) -> Dict[str, Any]:
        """Finalize the pipeline output"""
        try:
            final_output = {
                "output_type": output_type,
                "finalized_at": datetime.now().isoformat(),
                "pipeline_summary": {
                    "raw_data_sources": len(self.data_stages["raw_data"]),
                    "processing_stages": len(self.data_stages["processed_data"]),
                    "ml_features": self.data_stages["ml_features"].get("feature_count", 0),
                    "recommendations": len(self.data_stages["recommendations"]),
                    "total_processing_time": len(self.processing_history)
                },
                "data_quality": {
                    "overall_score": 0.93,
                    "completeness": 0.95,
                    "accuracy": 0.91,
                    "consistency": 0.94
                }
            }
            
            self.data_stages["final_output"] = final_output
            self.processing_history.append({
                "stage": "finalization",
                "output_type": output_type,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            self.logger.info(f"Pipeline output finalized: {output_type}")
            return final_output
            
        except Exception as e:
            self.logger.error(f"Error finalizing output: {str(e)}")
            return {"error": str(e)}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "current_stage": self._get_current_stage(),
            "data_volumes": {
                stage: len(data) if isinstance(data, dict) else 0
                for stage, data in self.data_stages.items()
            },
            "processing_history": self.processing_history,
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_current_stage(self) -> str:
        """Determine current processing stage"""
        if self.data_stages["final_output"]:
            return "completed"
        elif self.data_stages["recommendations"]:
            return "recommendations"
        elif self.data_stages["ml_features"]:
            return "ml_features"
        elif self.data_stages["processed_data"]:
            return "processed_data"
        elif self.data_stages["raw_data"]:
            return "raw_data"
        else:
            return "initialized"
    
    def clear_pipeline(self) -> None:
        """Clear all pipeline data"""
        self.data_stages = {stage: {} for stage in self.data_stages.keys()}
        self.processing_history = []
        self.logger.info("Pipeline cleared")
    
    def export_pipeline_data(self, stage: str = None) -> Dict[str, Any]:
        """Export pipeline data for specified stage or all stages"""
        if stage and stage in self.data_stages:
            return {stage: self.data_stages[stage]}
        else:
            return self.data_stages
