"""
Dashboard Builder for Travel Planner Analytics
Creates interactive dashboards for travel data visualization
"""

from typing import Dict, List, Any, Optional
import json

class DashboardBuilder:
    """Build interactive dashboards for travel analytics"""
    
    def __init__(self):
        self.dashboard_config = {
            "title": "Travel Planner Analytics Dashboard",
            "theme": "light",
            "layout": "grid"
        }
    
    def create_summary_dashboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary dashboard with key metrics"""
        try:
            dashboard = {
                "title": "Travel Summary Dashboard",
                "metrics": {
                    "total_places": data.get("total_places", 0),
                    "average_rating": data.get("average_rating", 0),
                    "total_cost": data.get("total_cost", 0),
                    "success_rate": data.get("success_rate", 0)
                },
                "charts": [
                    {
                        "type": "metric_card",
                        "title": "Total Places",
                        "value": data.get("total_places", 0),
                        "trend": "+5%"
                    },
                    {
                        "type": "metric_card", 
                        "title": "Average Rating",
                        "value": f"{data.get('average_rating', 0):.1f}",
                        "trend": "+0.2"
                    },
                    {
                        "type": "metric_card",
                        "title": "Total Cost",
                        "value": f"${data.get('total_cost', 0)}",
                        "trend": "-10%"
                    },
                    {
                        "type": "metric_card",
                        "title": "Success Rate",
                        "value": f"{data.get('success_rate', 0)}%",
                        "trend": "+2%"
                    }
                ]
            }
            return dashboard
        except Exception as e:
            return {"error": f"Error creating summary dashboard: {str(e)}"}
    
    def create_analytics_dashboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed analytics dashboard"""
        try:
            dashboard = {
                "title": "Detailed Analytics Dashboard",
                "sections": [
                    {
                        "title": "Rating Analysis",
                        "type": "histogram",
                        "data": data.get("rating_distribution", [])
                    },
                    {
                        "title": "Price Analysis", 
                        "type": "scatter",
                        "data": data.get("price_data", [])
                    },
                    {
                        "title": "Category Breakdown",
                        "type": "pie",
                        "data": data.get("category_data", [])
                    },
                    {
                        "title": "Trend Analysis",
                        "type": "line",
                        "data": data.get("trend_data", [])
                    }
                ]
            }
            return dashboard
        except Exception as e:
            return {"error": f"Error creating analytics dashboard: {str(e)}"}
    
    def create_comparison_dashboard(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison dashboard between two datasets"""
        try:
            dashboard = {
                "title": "Comparison Dashboard",
                "comparisons": [
                    {
                        "metric": "Average Rating",
                        "dataset1": data1.get("average_rating", 0),
                        "dataset2": data2.get("average_rating", 0),
                        "difference": abs(data1.get("average_rating", 0) - data2.get("average_rating", 0))
                    },
                    {
                        "metric": "Total Cost",
                        "dataset1": data1.get("total_cost", 0),
                        "dataset2": data2.get("total_cost", 0),
                        "difference": abs(data1.get("total_cost", 0) - data2.get("total_cost", 0))
                    },
                    {
                        "metric": "Success Rate",
                        "dataset1": data1.get("success_rate", 0),
                        "dataset2": data2.get("success_rate", 0),
                        "difference": abs(data1.get("success_rate", 0) - data2.get("success_rate", 0))
                    }
                ]
            }
            return dashboard
        except Exception as e:
            return {"error": f"Error creating comparison dashboard: {str(e)}"}
    
    def export_dashboard(self, dashboard: Dict[str, Any], format: str = "json") -> str:
        """Export dashboard in specified format"""
        try:
            if format == "json":
                return json.dumps(dashboard, indent=2)
            elif format == "html":
                return self._generate_html_dashboard(dashboard)
            else:
                return f"Unsupported format: {format}"
        except Exception as e:
            return f"Error exporting dashboard: {str(e)}"
    
    def _generate_html_dashboard(self, dashboard: Dict[str, Any]) -> str:
        """Generate HTML version of dashboard"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{dashboard.get('title', 'Dashboard')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric-card {{ 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 10px; 
            border-radius: 5px;
            display: inline-block;
            width: 200px;
        }}
        .metric-title {{ font-weight: bold; color: #333; }}
        .metric-value {{ font-size: 24px; color: #007bff; }}
        .metric-trend {{ color: #28a745; }}
    </style>
</head>
<body>
    <h1>{dashboard.get('title', 'Dashboard')}</h1>
"""
        
        if "metrics" in dashboard:
            html += "<div class='metrics'>"
            for key, value in dashboard["metrics"].items():
                html += f"""
                <div class="metric-card">
                    <div class="metric-title">{key.replace('_', ' ').title()}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """
            html += "</div>"
        
        html += """
</body>
</html>
"""
        return html
