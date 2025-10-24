"""
Populate Vector Database Script
================================
Load 50K+ places từ CSV vào ChromaDB Vector Database
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.vector_db_agent import get_vector_db_agent
import time


def populate_vector_database():
    """Populate vector database từ tất cả CSV files"""
    
    print("="*80)
    print("POPULATING VECTOR DATABASE")
    print("="*80)
    
    # Get agent
    agent = get_vector_db_agent()
    
    # Check current count
    stats = agent.get_database_stats()
    current_count = stats.get('total_documents', 0)
    
    print(f"\n📊 Current database state:")
    print(f"   Documents: {current_count}")
    
    if current_count > 0:
        print(f"\n⚠️  Database already has {current_count} documents. Re-populating...")
        # Auto-confirm for script execution
        
        # Clear existing data
        print(f"\n🗑️  Clearing existing collection...")
        agent.client.delete_collection(name=agent.collection_name)
        agent.collection = agent.client.create_collection(
            name=agent.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("   ✅ Collection cleared")
    
    # CSV files to load
    data_dir = Path(__file__).parent.parent / "data"
    csv_files = [
        "vietnam_all_places.csv",
        "hotels.csv",
        "hotels_large.csv",
        "restaurants.csv",
        "restaurants_large.csv",
        "attractions.csv",
        "attractions_large.csv",
        "entertainment.csv",
        "family.csv",
        "foodandbeverage.csv",
        "wellness.csv"
    ]
    
    print(f"\n📥 Loading data from {len(csv_files)} CSV files...")
    print(f"   Data directory: {data_dir}")
    
    total_added = 0
    start_time = time.time()
    
    for csv_file in csv_files:
        csv_path = data_dir / csv_file
        
        if not csv_path.exists():
            print(f"\n⚠️  File not found: {csv_file}")
            continue
        
        print(f"\n📄 Processing: {csv_file}")
        before_count = agent.collection.count()
        
        try:
            agent.add_places_from_csv(str(csv_path), batch_size=50)
            after_count = agent.collection.count()
            added = after_count - before_count
            total_added += added
            print(f"   ✅ Added {added} places from {csv_file}")
        
        except Exception as e:
            print(f"   ❌ Error processing {csv_file}: {e}")
    
    elapsed = time.time() - start_time
    
    # Final stats
    final_stats = agent.get_database_stats()
    
    print("\n" + "="*80)
    print("✅ POPULATION COMPLETED!")
    print("="*80)
    print(f"\n📊 Final Statistics:")
    print(f"   Total documents: {final_stats.get('total_documents', 0)}")
    print(f"   Documents added: {total_added}")
    print(f"   Time elapsed: {elapsed:.1f}s")
    print(f"   Cities: {len(final_stats.get('cities', []))}")
    print(f"   Categories: {len(final_stats.get('categories', []))}")
    
    if final_stats.get('cities'):
        print(f"\n🌆 Sample cities: {', '.join(list(final_stats['cities'])[:10])}")
    
    if final_stats.get('categories'):
        print(f"📂 Categories: {', '.join(list(final_stats['categories']))}")
    
    print("\n" + "="*80)
    print("🎉 Vector Database is ready for RAG!")
    print("="*80)


if __name__ == "__main__":
    populate_vector_database()

