"""
Multi-Agent System Orchestration using LangGraph
==================================================

Đây là file graph.py tổng thể kết nối TẤT CẢ các agent trong hệ thống Travel Planner / ViVu AI.

Kiến trúc hệ thống:
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1 - DATA COLLECTION                │
│  [API Collector] → [Web Scraper] → [Data Collector*]        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LAYER 2 - VALIDATION & PROCESSING              │
│  [Data Validator] → [Data Processor] → [Data Mapper] →       │
│  [Data Enricher] → [Data Import] → [VectorDB Agent]        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│            LAYER 3 - INTELLIGENCE & RAG                    │
│  [RAG Agent] → [VectorDB Agent] → [Destination Researcher] │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    LAYER 4 - PLANNING                       │
│  [Trip Planner Agent] → [Destination Research Agent]     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   LAYER 5 - ANALYTICS                       │
│  [Analytics Engine] → [Chat Assistant]                      │
└─────────────────────────────────────────────────────────────┘

* Data Collector: Thu thập dữ liệu thiếu từ web/APIs (optional, chỉ khi cần)

Workflows hỗ trợ:
1. DATA_PROCESSING - Xử lý CSV và import vào database
2. TRAVEL_PLANNING - Lập kế hoạch du lịch cho user
3. DESTINATION_RESEARCH - Nghiên cứu địa điểm
4. DATA_COLLECTION - Thu thập dữ liệu mới từ APIs/web
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Literal, Optional
from datetime import datetime
import uuid
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (TRAVEL_PLANNER directory)
    project_root = Path(__file__).resolve().parent
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, encoding='utf-8')
except ImportError:
    pass  # dotenv not available, continue without it
except Exception:
    pass  # Continue if .env can't be loaded

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# LangSmith configuration - Use centralized config
from config.langsmith_config import get_langsmith_config
_langsmith_config = get_langsmith_config()  # Initialize on import

# Import state definitions
from agents.state import TravelState
from agents.data_processing_state import DataProcessingState

# Import all agents
# Layer 1: Data Collection
from agents.api_collector import APICollectorAgent
from agents.web_scraper import WebScraperAgent
from agents.data_collector_agent import DataCollectorAgent

# Layer 2: Validation & Processing
from agents.data_validator_agent import DataValidatorAgent
from agents.data_processor import DataProcessorAgent
from agents.data_mapper_agent import DataMapperAgent
from agents.travel_agents.vector_db import VectorDatabaseAgent

# Layer 3: Intelligence & RAG (optional imports for travel planning)
try:
    from agents.travel_agents.rag import RAGAgent
except ImportError:
    RAGAgent = None

# Layer 4: Planning (optional imports for travel planning)
try:
    from agents.trip_planner import TripPlannerAgent
    from agents.destination_researcher import DestinationResearchAgent
except ImportError:
    TripPlannerAgent = None
    DestinationResearchAgent = None

# Layer 5: Analytics (optional imports for travel planning)
try:
    from agents.analytics import AnalyticsEngineAgent
except ImportError:
    AnalyticsEngineAgent = None

# Chat Assistant is a separate service, not part of the main workflow

# Data processing workflow agents (Layer 1-2 cho CSV processing)
from agents.data_processing_state import DataProcessingState

logger = logging.getLogger(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ============================================================================
# WORKFLOW 1: DATA PROCESSING (CSV → Database)
# ============================================================================

# Import data processing functions from previous implementation
async def load_csv_data(state: DataProcessingState) -> DataProcessingState:
    """Load CSV data into state."""
    import pandas as pd
    logger.info("Loading CSV data...")
    
    csv_path = state.get('csv_file_path')
    if not csv_path:
        state['errors'] = state.get('errors', []) + [{
            'step': 'load_csv',
            'error': 'No CSV file path provided'
        }]
        return state
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
        
        # Apply limit if specified
        limit = state.get('_limit')
        if limit:
            df = df.head(limit)
            logger.info(f"Limited to {limit} records for processing")
        
        records = df.to_dict('records')
        state['raw_records'] = records
        state['stats'] = {
            'total_records': len(records),
            'columns': list(df.columns)
        }
        logger.info(f"Loaded {len(records)} records from CSV")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        state['errors'] = state.get('errors', []) + [{
            'step': 'load_csv',
            'error': str(e)
        }]
    
    return state


async def validate_data(state: DataProcessingState) -> DataProcessingState:
    """Validate data using DataValidatorAgent."""
    logger.info("Validating data...")
    
    state['current_agent'] = 'data_validator'
    state['current_step'] = 'validation'
    
    raw_records = state.get('raw_records', [])
    if not raw_records:
        return state
    
    try:
        validator_agent = DataValidatorAgent()
        records_to_validate = []
        for record in raw_records:
            # Keep original record and add mapped fields
            mapped = record.copy()  # Preserve all original CSV fields
            # Add mapped fields for validation
            mapped['tenDiaDiem'] = record.get('name', '')
            mapped['maTinhThanh'] = record.get('city', '')  # Keep city name here
            mapped['loaiDiaDiem'] = record.get('category', '')
            mapped['viDo'] = record.get('latitude')
            mapped['kinhDo'] = record.get('longitude')
            mapped['moTa'] = record.get('description', '')
            mapped['giaVe'] = record.get('price_level')
            mapped['dienThoai'] = record.get('phone', '')
            mapped['website'] = record.get('website', '')
            records_to_validate.append(mapped)
        
        validation_result = validator_agent.validate_batch(records_to_validate)
        
        state['validated_records'] = validation_result.get('valid', [])
        state['validation_errors'] = validation_result.get('invalid', [])
        state['_original_records_for_mapping'] = raw_records
        state['completed_steps'] = state.get('completed_steps', []) + ['validation']
        
        logger.info(f"Validation complete: {len(state['validated_records'])} valid records")
        
    except Exception as e:
        logger.error(f"Error in validation: {e}")
        state['errors'] = state.get('errors', []) + [{
            'step': 'validation',
            'error': str(e)
        }]
    
    return state


# Additional data processing nodes (simplified - use full implementation from data processing workflow)
async def enrich_with_missing_data(state: DataProcessingState) -> DataProcessingState:
    """Enrich records with collected data (optional step)."""
    logger.info("Enriching data with missing information...")
    
    try:
        # Use DataCollectorAgent if there are missing valuable fields
        missing_fields = state.get('missing_fields', {})
        valuable_fields = ['diaChi', 'dienThoai', 'website', 'gioMoCua', 'viDo', 'kinhDo']
        missing_count = sum(
            len(indices) for field, indices in missing_fields.items() 
            if field in valuable_fields
        )
        
        if missing_count > 0:
            logger.info(f"Found {missing_count} missing valuable fields, enriching...")
            collector = DataCollectorAgent()
            collected_state = await collector.execute(state)
            state.update(collected_state)
            
            # Merge collected data into validated records
            validated = state.get('validated_records', [])
            collected_data = state.get('collected_data', {})
            
            enriched_records = []
            for idx, record in enumerate(validated):
                enriched = record.copy()
                collected = collected_data.get(str(idx), {})
                
                # Merge collected data (only if field is missing)
                for key, value in collected.items():
                    if not enriched.get(key) and value:
                        enriched[key] = value
                
                enriched_records.append(enriched)
            
            state['enriched_records'] = enriched_records
            state['completed_steps'] = state.get('completed_steps', []) + ['enrichment']
        else:
            logger.info("No enrichment needed")
            state['enriched_records'] = state.get('validated_records', [])
        
    except Exception as e:
        logger.error(f"Error in enrichment: {e}")
        # Continue without enrichment
        state['enriched_records'] = state.get('validated_records', [])
        state['warnings'] = state.get('warnings', []) + [{
            'step': 'enrichment',
            'warning': f"Enrichment failed: {str(e)}"
        }]
    
    return state


async def process_and_import_data(state: DataProcessingState) -> DataProcessingState:
    """Process and import data - combines mapping and import."""
    logger.info("Processing and importing data...")
    
    try:
        from agents.data_mapper_agent import DataMapperAgent
        from agents.base_agent import BaseAgent
        
        # Step 1: Enrich data if needed
        state = await enrich_with_missing_data(state)
        
        # Step 2: Map records to database schema
        logger.info("Mapping records to database schema...")
        mapper = DataMapperAgent()
        
        # Prepare state for mapper - use enriched or validated records
        temp_state = state.copy()
        if not temp_state.get('enriched_records'):
            temp_state['enriched_records'] = state.get('validated_records', [])
        
        mapped_state = await mapper.execute(temp_state)
        state.update(mapped_state)
        
        mapped_records = state.get('mapped_records', [])
        logger.info(f"Mapped {len(mapped_records)} records")
        
        # Step 3: Classify places using LLM (optional, can be disabled)
        classify_places = state.get('classify_places', True)  # Default to True
        if classify_places and mapped_records:
            logger.info("Classifying places into tourism categories...")
            try:
                from agents.place_classifier_agent import PlaceClassifierAgent
                classifier = PlaceClassifierAgent()
                
                # Classify in batches
                batch_size = 20  # Smaller batch for LLM calls
                classified_count = 0
                
                for i in range(0, len(mapped_records), batch_size):
                    batch = mapped_records[i:i + batch_size]
                    logger.info(f"  Classifying batch {i // batch_size + 1} ({len(batch)} places)...")
                    
                    for record in batch:
                        try:
                            # Get existing dacDiem
                            existing_dac_diem = {}
                            if record.get('dacDiem'):
                                try:
                                    existing_dac_diem = json.loads(record['dacDiem'])
                                except:
                                    pass
                            
                            # Skip if already classified
                            if existing_dac_diem.get('danh_muc'):
                                continue
                            
                            # Get city name if not available
                            tinh_thanh_name = record.get('maTinhThanh_name', '')
                            if not tinh_thanh_name and record.get('maTinhThanh'):
                                # Try to get from city mapping if available
                                # If maTinhThanh is an ID, we'd need to query, but skip for now
                                pass
                            
                            # Classify
                            classification = classifier.classify_place(
                                ten_dia_diem=record.get('tenDiaDiem', ''),
                                loai_dia_diem=record.get('loaiDiaDiem', 'khac'),
                                mo_ta=record.get('moTa', ''),
                                dia_chi=record.get('diaChi', ''),
                                tinh_thanh=tinh_thanh_name or record.get('city', ''),
                                additional_info=existing_dac_diem
                            )
                            
                            # Update dacDiem with classification
                            updated_dac_diem = classifier.update_place_dac_diem(
                                classification, existing_dac_diem
                            )
                            record['dacDiem'] = json.dumps(updated_dac_diem, ensure_ascii=False)
                            classified_count += 1
                            
                        except Exception as e:
                            logger.warning(f"  Failed to classify record {record.get('tenDiaDiem', 'unknown')}: {e}")
                            # Continue with other records
                
                logger.info(f"  Classified {classified_count} places")
                state['classified_count'] = classified_count
                
            except Exception as e:
                logger.warning(f"Classification step failed: {e}. Continuing without classification...")
                state['classification_error'] = str(e)
        
        # Step 4: Import to database
        logger.info("Importing to database...")
        
        class DataImportAgent(BaseAgent):
            def __init__(self):
                super().__init__("data_import", "Imports data into DIADIEM table")
            
            async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
                import django
                from django.apps import apps as django_apps
                import sys
                from pathlib import Path
                
                backend_path = Path(__file__).parent.parent / 'vivu_backend'
                if str(backend_path) not in sys.path:
                    sys.path.insert(0, str(backend_path))
                
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
                if not django_apps.ready:
                    django.setup()
                
                from asgiref.sync import sync_to_async
                from apps.places.models import DiaDiem
                
                mapped_records = state.get('mapped_records', [])
                
                def import_records_sync(records):
                    imported = failed = skipped = 0
                    errors_detail = []
                    
                    for idx, record in enumerate(records):
                        try:
                            # Validate required fields
                            if not record.get('tenDiaDiem'):
                                failed += 1
                                errors_detail.append(f"Record {idx}: Missing tenDiaDiem")
                                continue
                            
                            if not record.get('maTinhThanh'):
                                failed += 1
                                errors_detail.append(f"Record {idx}: Missing maTinhThanh")
                                continue
                            
                            # Check for duplicates
                            # Method 1: Check by name + city (exact match)
                            existing = DiaDiem.objects.filter(
                                tenDiaDiem=record['tenDiaDiem'],
                                maTinhThanh=record['maTinhThanh']
                            ).first()
                            
                            if existing:
                                skipped += 1
                                continue
                            
                            # Method 2: Check by coordinates (if available)
                            # This prevents duplicate places with same coordinates but slightly different names
                            vi_do = record.get('viDo')
                            kinh_do = record.get('kinhDo')
                            if vi_do and kinh_do:
                                # Round to 0.0001 degrees (~11 meters) to catch nearby duplicates
                                tolerance = 0.0001
                                lat_rounded = round(vi_do / tolerance) * tolerance
                                lon_rounded = round(kinh_do / tolerance) * tolerance
                                
                                existing_by_coords = DiaDiem.objects.filter(
                                    viDo__gte=lat_rounded - tolerance,
                                    viDo__lte=lat_rounded + tolerance,
                                    kinhDo__gte=lon_rounded - tolerance,
                                    kinhDo__lte=lon_rounded + tolerance,
                                    maTinhThanh=record['maTinhThanh']
                                ).first()
                                
                                if existing_by_coords:
                                    # Check if names are similar (likely duplicate)
                                    name1 = record['tenDiaDiem'].lower().strip()
                                    name2 = existing_by_coords.tenDiaDiem.lower().strip()
                                    
                                    # If names are very similar (same or one is substring of other), skip
                                    if (name1 == name2 or 
                                        name1 in name2 or name2 in name1 or
                                        abs(len(name1) - len(name2)) < 3):
                                        skipped += 1
                                        continue
                            
                            # Ensure loaiDiaDiem is valid
                            valid_loai = ['dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac']
                            if record.get('loaiDiaDiem') not in valid_loai:
                                record['loaiDiaDiem'] = 'khac'
                            
                            # Ensure trangThai is valid
                            valid_trang_thai = ['active', 'inactive', 'pending']
                            if record.get('trangThai') not in valid_trang_thai:
                                record['trangThai'] = 'active'
                            
                            # Clean data - remove None values for optional fields
                            clean_record = {k: v for k, v in record.items() if v is not None or k in ['tenDiaDiem', 'maTinhThanh', 'loaiDiaDiem']}
                            
                            # Create record
                            DiaDiem.objects.create(**clean_record)
                            imported += 1
                            
                            if imported % 100 == 0:
                                logger.info(f"  Imported {imported} records...")
                                
                        except Exception as e:
                            failed += 1
                            error_msg = f"Record {idx} ({record.get('tenDiaDiem', 'unknown')}): {str(e)}"
                            errors_detail.append(error_msg)
                            if len(errors_detail) <= 20:  # Limit error details
                                logger.error(error_msg)
                    
                    return {
                        'total': len(records),
                        'imported': imported,
                        'failed': failed,
                        'skipped': skipped,
                        'errors_detail': errors_detail[:20]  # First 20 errors
                    }
                
                import_async = sync_to_async(import_records_sync)
                import_summary = await import_async(mapped_records)
                
                state['import_summary'] = import_summary
                state['ready_for_import'] = True
                return state
        
        import_agent = DataImportAgent()
        import_state = await import_agent.execute(state)
        state.update(import_state)
        state['completed_steps'] = state.get('completed_steps', []) + ['mapping', 'import']
        
        logger.info(f"Import complete: {import_state['import_summary']['imported']} imported, "
                   f"{import_state['import_summary']['failed']} failed, "
                   f"{import_state['import_summary']['skipped']} skipped")
        
    except Exception as e:
        logger.error(f"Error in process/import: {e}", exc_info=True)
        state['errors'] = state.get('errors', []) + [{
            'step': 'process_import',
            'error': str(e)
        }]
    
    return state


# ============================================================================
# WORKFLOW 2: TRAVEL PLANNING
# ============================================================================

async def collect_travel_data(state: TravelState) -> TravelState:
    """Layer 1: Collect data from APIs and web."""
    logger.info("Collecting travel data...")
    
    try:
        api_agent = APICollectorAgent()
        web_agent = WebScraperAgent()
        
        api_result = await api_agent.execute(state)
        state.update(api_result)
        
        web_result = await web_agent.execute(state)
        state.update(web_result)
        
        state['completed_agents'] = state.get('completed_agents', []) + ['api_collector', 'web_scraper']
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        state['errors'] = state.get('errors', []) + [{
            'agent': 'data_collection',
            'error': str(e)
        }]
    
    return state


async def process_travel_data(state: TravelState) -> TravelState:
    """Layer 2: Process and validate collected data."""
    logger.info("Processing travel data...")
    
    try:
        processor = DataProcessorAgent()
        result = await processor.execute(state)
        state.update(result)
        state['completed_agents'].append('data_processor')
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        state['errors'].append({
            'agent': 'data_processor',
            'error': str(e)
        })
    
    return state


async def embed_travel_data(state: TravelState) -> TravelState:
    """Layer 2/3: Embed data into vector database."""
    logger.info("Embedding data into vector DB...")
    
    try:
        vector_agent = VectorDatabaseAgent()
        # VectorDB agent methods would be called here
        # For now, just mark as completed
        state['completed_agents'].append('vector_db')
    except Exception as e:
        logger.error(f"Error embedding data: {e}")
        state['errors'].append({
            'agent': 'vector_db',
            'error': str(e)
        })
    
    return state


async def research_destinations(state: TravelState) -> TravelState:
    """Layer 3/4: Research destinations using RAG."""
    logger.info("Researching destinations...")
    
    try:
        rag_agent = RAGAgent()
        researcher = DestinationResearchAgent()
        
        # Use RAG to get context
        query = f"Places to visit in {', '.join(state.get('cities', []))}"
        rag_context = rag_agent.query(query)
        state['rag_context'] = rag_context
        
        # Research with agent
        research_result = await researcher.execute(state)
        state.update(research_result)
        state['completed_agents'].extend(['rag', 'destination_researcher'])
    except Exception as e:
        logger.error(f"Error researching: {e}")
        state['errors'].append({
            'agent': 'destination_research',
            'error': str(e)
        })
    
    return state


async def plan_itinerary(state: TravelState) -> TravelState:
    """Layer 4: Create travel itinerary."""
    logger.info("Planning itinerary...")
    
    try:
        planner = TripPlannerAgent()
        result = await planner.execute(state)
        state.update(result)
        state['completed_agents'].append('trip_planner')
    except Exception as e:
        logger.error(f"Error planning: {e}")
        state['errors'].append({
            'agent': 'trip_planner',
            'error': str(e)
        })
    
    return state


async def analyze_and_refine(state: TravelState) -> TravelState:
    """Layer 5: Analytics and final refinement."""
    logger.info("Analyzing and refining...")
    
    try:
        analytics = AnalyticsEngineAgent()
        result = await analytics.execute(state)
        state.update(result)
        state['completed_agents'].append('analytics')
    except Exception as e:
        logger.error(f"Error in analytics: {e}")
        state['errors'].append({
            'agent': 'analytics',
            'error': str(e)
        })
    
    return state


# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def should_collect_missing_data(state: DataProcessingState) -> Literal["collect", "skip_collect"]:
    """Decide whether to collect missing data."""
    missing_fields = state.get('missing_fields', {})
    valuable_fields = ['diaChi', 'dienThoai', 'website', 'gioMoCua', 'viDo', 'kinhDo']
    missing_count = sum(
        len(indices) for field, indices in missing_fields.items() 
        if field in valuable_fields
    )
    return "collect" if missing_count > 0 else "skip_collect"


def route_workflow(state: Dict[str, Any]) -> Literal["data_processing", "travel_planning"]:
    """Route to appropriate workflow based on state."""
    if 'csv_file_path' in state or 'raw_records' in state:
        return "data_processing"
    return "travel_planning"


# ============================================================================
# CREATE GRAPHS
# ============================================================================

def create_data_processing_graph():
    """Create LangGraph workflow for CSV data processing."""
    
    workflow = StateGraph(DataProcessingState)
    
    # Add nodes
    workflow.add_node("load_csv", load_csv_data)
    workflow.add_node("validate", validate_data)
    workflow.add_node("process_import", process_and_import_data)
    
    # Set entry point
    workflow.set_entry_point("load_csv")
    
    # Add edges
    workflow.add_edge("load_csv", "validate")
    workflow.add_edge("validate", "process_import")
    workflow.add_edge("process_import", END)
    
    # Compile with memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def create_travel_planning_graph():
    """Create LangGraph workflow for travel planning."""
    
    workflow = StateGraph(TravelState)
    
    # Layer 1: Data Collection
    workflow.add_node("collect_data", collect_travel_data)
    
    # Layer 2: Processing
    workflow.add_node("process_data", process_travel_data)
    workflow.add_node("embed_data", embed_travel_data)
    
    # Layer 3/4: Intelligence & Planning
    workflow.add_node("research", research_destinations)
    workflow.add_node("plan", plan_itinerary)
    
    # Layer 5: Analytics
    workflow.add_node("analyze", analyze_and_refine)
    
    # Define workflow
    workflow.set_entry_point("collect_data")
    workflow.add_edge("collect_data", "process_data")
    workflow.add_edge("process_data", "embed_data")
    workflow.add_edge("embed_data", "research")
    workflow.add_edge("research", "plan")
    workflow.add_edge("plan", "analyze")
    workflow.add_edge("analyze", END)
    
    # Compile with memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def create_master_graph():
    """
    Create master graph that routes to appropriate workflow.
    This is the main entry point for the entire system.
    """
    
    # Combined state type (union of both)
    from typing import TypedDict, Union
    
    class MasterState(TypedDict, total=False):
        """Master state that can handle both workflows."""
        workflow_type: Literal["data_processing", "travel_planning"]
        # Data processing fields
        csv_file_path: Optional[str]
        raw_records: List[Dict[str, Any]]
        # Travel planning fields
        user_id: Optional[int]
        cities: List[str]
        start_date: str
        end_date: str
        budget_max: float
        interests: List[str]
        # Common fields
        workflow_id: str
        errors: List[Dict[str, Any]]
        completed_agents: List[str]
    
    workflow = StateGraph(MasterState)
    
    # Add routing node
    def route(state: MasterState) -> Literal["data_processing", "travel_planning"]:
        return route_workflow(state)
    
    # Note: In practice, you'd want to handle both workflows separately
    # For simplicity, we return the appropriate graph
    return None  # Use specific graphs instead


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

async def process_csv_to_database(csv_file_path: str, limit: int = None) -> Dict[str, Any]:
    """
    Process CSV and import to database.
    
    Args:
        csv_file_path: Path to CSV file
        limit: Limit number of records to process (None = all)
        
    Returns:
        Processing results
    """
    logger.info(f"Starting data processing workflow for: {csv_file_path}")
    if limit:
        logger.info(f"Limited to {limit} records")
    
    app = create_data_processing_graph()
    
    initial_state: DataProcessingState = {
        'csv_file_path': csv_file_path,
        'workflow_id': str(uuid.uuid4()),
        'raw_records': [],
        'validated_records': [],
        'enriched_records': [],
        'mapped_records': [],
        'validation_errors': [],
        'missing_fields': {},
        'current_agent': '',
        'current_step': '',
        'errors': [],
        'warnings': [],
        'completed_steps': [],
        'stats': {},
        'ready_for_import': False,
        'import_summary': {},
        '_limit': limit  # Store limit in state
    }
    
    config = {
        'configurable': {
            'thread_id': initial_state['workflow_id']
        }
    }
    
    try:
        final_state = await app.ainvoke(initial_state, config)
        
        summary = {
            'workflow_id': final_state.get('workflow_id'),
            'total_records': len(final_state.get('raw_records', [])),
            'validated': len(final_state.get('validated_records', [])),
            'mapped': len(final_state.get('mapped_records', [])),
            'import_summary': final_state.get('import_summary', {}),
            'errors': final_state.get('errors', []),
            'completed_steps': final_state.get('completed_steps', []),
            'success': len(final_state.get('errors', [])) == 0
        }
        
        logger.info(f"Workflow complete: {summary}")
        return {'state': final_state, 'summary': summary}
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return {'error': str(e), 'state': initial_state, 'success': False}


async def plan_travel(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan travel itinerary.
    
    Args:
        user_input: User requirements (cities, dates, budget, etc.)
        
    Returns:
        Travel plan with itinerary
    """
    logger.info("Starting travel planning workflow")
    
    app = create_travel_planning_graph()
    
    initial_state: TravelState = {
        'workflow_id': str(uuid.uuid4()),
        'current_agent': 'collect_data',
        'errors': [],
        'completed_agents': [],
        **user_input
    }
    
    config = {
        'configurable': {
            'thread_id': initial_state['workflow_id']
        }
    }
    
    try:
        final_state = await app.ainvoke(initial_state, config)
        
        summary = {
            'workflow_id': final_state.get('workflow_id'),
            'itinerary': final_state.get('itinerary'),
            'recommendations': final_state.get('recommendations', []),
            'analytics': final_state.get('analytics'),
            'errors': final_state.get('errors', []),
            'completed_agents': final_state.get('completed_agents', []),
            'success': len(final_state.get('errors', [])) == 0
        }
        
        logger.info("Travel planning workflow complete")
        return {'state': final_state, 'summary': summary}
        
    except Exception as e:
        logger.error(f"Travel planning failed: {e}", exc_info=True)
        return {'error': str(e), 'state': initial_state, 'success': False}


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "travel":
        # Travel planning mode
        user_input = {
            'cities': ['Hanoi', 'Ho Chi Minh City'],
            'start_date': '2025-01-01',
            'end_date': '2025-01-07',
            'budget_max': 10000000,
            'interests': ['cultural', 'food'],
            'group_size': 2,
            'travel_style': 'moderate'
        }
        result = asyncio.run(plan_travel(user_input))
        print(f"\nTravel Planning Result: {result.get('summary', {})}")
    
    else:
        # Data processing mode (default)
        csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/vietnam_all_places.csv"
        result = asyncio.run(process_csv_to_database(csv_path))
        
        if result.get('success'):
            summary = result.get('summary', {})
            print("\n" + "="*60)
            print("DATA PROCESSING COMPLETE")
            print("="*60)
            print(f"Total Records: {summary.get('total_records', 0)}")
            print(f"Validated: {summary.get('validated', 0)}")
            print(f"Mapped: {summary.get('mapped', 0)}")
            import_summary = summary.get('import_summary', {})
            print(f"Imported: {import_summary.get('imported', 0)}")
            print(f"Failed: {import_summary.get('failed', 0)}")
            print(f"Skipped: {import_summary.get('skipped', 0)}")
            print("="*60)
        else:
            print(f"\nERROR: {result.get('error')}")
