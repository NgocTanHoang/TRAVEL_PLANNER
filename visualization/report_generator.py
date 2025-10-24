"""
Report Generator for Travel Planner Analytics
Generates comprehensive reports from travel data analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ReportGenerator:
    """Generate comprehensive reports from travel analytics"""
    
    def __init__(self):
        self.report_templates = {
            "summary": self._generate_summary_report,
            "detailed": self._generate_detailed_report,
            "comparison": self._generate_comparison_report
        }
    
    def generate_report(self, data: Dict[str, Any], report_type: str = "summary") -> Dict[str, Any]:
        """Generate report of specified type"""
        try:
            if report_type in self.report_templates:
                return self.report_templates[report_type](data)
            else:
                return {"error": f"Unknown report type: {report_type}"}
        except Exception as e:
            return {"error": f"Error generating report: {str(e)}"}
    
    def _generate_summary_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report"""
        report = {
            "title": "Travel Planning Summary Report",
            "generated_at": datetime.now().isoformat(),
            "executive_summary": {
                "total_places_analyzed": data.get("total_places", 0),
                "average_rating": data.get("average_rating", 0),
                "total_cost_estimate": data.get("total_cost", 0),
                "success_rate": data.get("success_rate", 0)
            },
            "key_findings": [
                f"Analyzed {data.get('total_places', 0)} places",
                f"Average rating: {data.get('average_rating', 0):.1f}/5.0",
                f"Total cost estimate: ${data.get('total_cost', 0)}",
                f"Success rate: {data.get('success_rate', 0)}%"
            ],
            "recommendations": [
                "Focus on high-rated establishments",
                "Consider budget-friendly alternatives",
                "Plan activities based on user preferences",
                "Monitor success metrics regularly"
            ]
        }
        return report
    
    def _generate_detailed_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed analysis report"""
        report = {
            "title": "Detailed Travel Analysis Report",
            "generated_at": datetime.now().isoformat(),
            "analysis_sections": {
                "rating_analysis": {
                    "average_rating": data.get("average_rating", 0),
                    "rating_distribution": data.get("rating_distribution", []),
                    "top_rated_places": data.get("top_rated_places", [])
                },
                "cost_analysis": {
                    "total_cost": data.get("total_cost", 0),
                    "cost_breakdown": data.get("cost_breakdown", {}),
                    "budget_optimization": data.get("budget_optimization", {})
                },
                "category_analysis": {
                    "category_distribution": data.get("category_distribution", {}),
                    "popular_categories": data.get("popular_categories", []),
                    "category_performance": data.get("category_performance", {})
                }
            },
            "insights": [
                "Rating distribution shows positive skew",
                "Cost optimization opportunities identified",
                "Category preferences vary by user type",
                "Success metrics indicate good performance"
            ],
            "action_items": [
                "Implement rating-based filtering",
                "Add cost optimization features",
                "Enhance category recommendations",
                "Monitor performance metrics"
            ]
        }
        return report
    
    def _generate_comparison_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison report"""
        report = {
            "title": "Travel Planning Comparison Report",
            "generated_at": datetime.now().isoformat(),
            "comparison_metrics": {
                "rating_comparison": {
                    "current": data.get("current_rating", 0),
                    "previous": data.get("previous_rating", 0),
                    "change": data.get("rating_change", 0)
                },
                "cost_comparison": {
                    "current": data.get("current_cost", 0),
                    "previous": data.get("previous_cost", 0),
                    "change": data.get("cost_change", 0)
                },
                "performance_comparison": {
                    "current": data.get("current_performance", 0),
                    "previous": data.get("previous_performance", 0),
                    "change": data.get("performance_change", 0)
                }
            },
            "trend_analysis": {
                "rating_trend": "improving" if data.get("rating_change", 0) > 0 else "declining",
                "cost_trend": "increasing" if data.get("cost_change", 0) > 0 else "decreasing",
                "performance_trend": "improving" if data.get("performance_change", 0) > 0 else "declining"
            },
            "recommendations": [
                "Continue current strategy if trends are positive",
                "Adjust approach if trends are negative",
                "Monitor key metrics regularly",
                "Implement improvements based on analysis"
            ]
        }
        return report
    
    def export_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """Export report in specified format"""
        try:
            if format == "json":
                return json.dumps(report, indent=2)
            elif format == "text":
                return self._generate_text_report(report)
            elif format == "html":
                return self._generate_html_report(report)
            else:
                return f"Unsupported format: {format}"
        except Exception as e:
            return f"Error exporting report: {str(e)}"
    
    def _generate_text_report(self, report: Dict[str, Any]) -> str:
        """Generate text version of report"""
        text = f"""
{report.get('title', 'Report')}
Generated: {report.get('generated_at', 'Unknown')}

"""
        
        if "executive_summary" in report:
            text += "EXECUTIVE SUMMARY\n"
            text += "=" * 50 + "\n"
            for key, value in report["executive_summary"].items():
                text += f"{key.replace('_', ' ').title()}: {value}\n"
            text += "\n"
        
        if "key_findings" in report:
            text += "KEY FINDINGS\n"
            text += "=" * 50 + "\n"
            for finding in report["key_findings"]:
                text += f"• {finding}\n"
            text += "\n"
        
        if "recommendations" in report:
            text += "RECOMMENDATIONS\n"
            text += "=" * 50 + "\n"
            for rec in report["recommendations"]:
                text += f"• {rec}\n"
            text += "\n"
        
        return text
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML version of report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.get('title', 'Report')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .findings {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{report.get('title', 'Report')}</h1>
    <p>Generated: {report.get('generated_at', 'Unknown')}</p>
"""
        
        if "executive_summary" in report:
            html += "<div class='summary'><h2>Executive Summary</h2>"
            for key, value in report["executive_summary"].items():
                html += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            html += "</div>"
        
        if "key_findings" in report:
            html += "<div class='findings'><h2>Key Findings</h2><ul>"
            for finding in report["key_findings"]:
                html += f"<li>{finding}</li>"
            html += "</ul></div>"
        
        if "recommendations" in report:
            html += "<div class='recommendations'><h2>Recommendations</h2><ul>"
            for rec in report["recommendations"]:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"
        
        html += """
</body>
</html>
"""
        return html
