"""
Script tổng hợp để load tất cả datasets vào Vector DB
======================================================
Load cả Kaggle dataset và GitHub Excel dataset
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_all_datasets():
    """Load tất cả datasets vào Vector DB"""
    
    print("="*80)
    print("LOADING ALL DATASETS INTO VECTOR DB")
    print("="*80)
    print()
    
    success_count = 0
    total_count = 2
    
    # 1. Load Kaggle Vietnam tourism v2 dataset
    print("\n" + "="*80)
    print("1. LOADING KAGGLE VIETNAM TOURISM V2 DATASET")
    print("="*80)
    try:
        from scripts.load_kaggle_dataset import load_dataset_to_vector_db, DATASET_URL as KAGGLE_URL
        
        data_dir = Path(__file__).resolve().parent.parent / "data"
        json_path = data_dir / "train_vietnam_tourism.json"
        
        if json_path.exists():
            print(f"📁 Found existing Kaggle dataset: {json_path}")
            response = input("   Load Kaggle dataset? (y/n): ").strip().lower()
            if response == 'y':
                if load_dataset_to_vector_db(json_path=json_path, batch_size=100):
                    success_count += 1
                    print("✅ Kaggle dataset loaded successfully!")
                else:
                    print("❌ Failed to load Kaggle dataset")
        else:
            response = input("   Download and load Kaggle dataset? (y/n): ").strip().lower()
            if response == 'y':
                if load_dataset_to_vector_db(json_path=None, download_url=KAGGLE_URL, batch_size=100):
                    success_count += 1
                    print("✅ Kaggle dataset loaded successfully!")
                else:
                    print("❌ Failed to load Kaggle dataset")
            else:
                print("⏭️  Skipped Kaggle dataset")
    except Exception as e:
        logger.error(f"Error loading Kaggle dataset: {e}")
        print(f"❌ Error: {e}")
    
    # 2. Load GitHub Excel dataset
    print("\n" + "="*80)
    print("2. LOADING GITHUB EXCEL DATASET (63 TỈNH THÀNH)")
    print("="*80)
    try:
        from scripts.load_github_excel_dataset import load_excel_dataset_to_vector_db, DATASET_URL as EXCEL_URL
        
        data_dir = Path(__file__).resolve().parent.parent / "data"
        excel_path = data_dir / "DataSet.xlsx"
        
        if excel_path.exists():
            print(f"📁 Found existing Excel dataset: {excel_path}")
            response = input("   Load Excel dataset? (y/n): ").strip().lower()
            if response == 'y':
                if load_excel_dataset_to_vector_db(excel_path=excel_path, batch_size=100):
                    success_count += 1
                    print("✅ Excel dataset loaded successfully!")
                else:
                    print("❌ Failed to load Excel dataset")
        else:
            response = input("   Download and load Excel dataset? (y/n): ").strip().lower()
            if response == 'y':
                if load_excel_dataset_to_vector_db(excel_path=None, download_url=EXCEL_URL, batch_size=100):
                    success_count += 1
                    print("✅ Excel dataset loaded successfully!")
                else:
                    print("❌ Failed to load Excel dataset")
            else:
                print("⏭️  Skipped Excel dataset")
    except Exception as e:
        logger.error(f"Error loading Excel dataset: {e}")
        print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Successfully loaded: {success_count}/{total_count} datasets")
    
    if success_count > 0:
        # Get final stats
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            vector_db = get_vector_db_agent()
            stats = vector_db.get_database_stats()
            
            print(f"\n📊 Vector DB Statistics:")
            print(f"   Total documents: {stats.get('total_documents', 0)}")
            print(f"   Cities: {len(stats.get('cities', []))}")
            print(f"   Categories: {len(stats.get('categories', []))}")
            
            if stats.get('cities'):
                print(f"\n   Sample cities: {', '.join(list(stats['cities'])[:15])}")
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
    
    print("\n" + "="*80)
    if success_count == total_count:
        print("✅ ALL DATASETS LOADED SUCCESSFULLY!")
    elif success_count > 0:
        print("⚠️  SOME DATASETS LOADED SUCCESSFULLY")
    else:
        print("❌ NO DATASETS LOADED")
    print("="*80)
    
    return success_count == total_count


if __name__ == "__main__":
    success = load_all_datasets()
    sys.exit(0 if success else 1)

