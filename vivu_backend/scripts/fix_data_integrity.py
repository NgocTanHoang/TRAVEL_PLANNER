"""
Script to fix data integrity issues in the database.
"""
import os
import sys
import django

# Add the project directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vivu_backend'))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

def check_hinhanhdiadiem():
    """Check for invalid references in HINHANHDIADIEM table."""
    from django.db import connection
    from django.db.utils import OperationalError
    
    try:
        with connection.cursor() as cursor:
            # Find images that reference non-existent DiaDiem records
            cursor.execute("""
                SELECT hd.maHinhAnh, hd.maDiaDiem 
                FROM HINHANHDIADIEM hd
                LEFT JOIN DIADIEM d ON hd.maDiaDiem = d.maDiaDiem
                WHERE d.maDiaDiem IS NULL
            """)
            invalid_references = cursor.fetchall()
            
            if not invalid_references:
                print("No invalid references found in HINHANHDIADIEM table.")
                return
                
            print(f"Found {len(invalid_references)} invalid references in HINHANHDIADIEM table:")
            for img_id, diadiem_id in invalid_references:
                print(f"- Image ID {img_id} references non-existent DiaDiem ID {diadiem_id}")
                
            # Ask for confirmation before deleting
            confirm = input("\nDo you want to delete these invalid references? (y/n): ")
            if confirm.lower() == 'y':
                cursor.execute("""
                    DELETE FROM HINHANHDIADIEM
                    WHERE maHinhAnh IN (
                        SELECT hd.maHinhAnh
                        FROM HINHANHDIADIEM hd
                        LEFT JOIN DIADIEM d ON hd.maDiaDiem = d.maDiaDiem
                        WHERE d.maDiaDiem IS NULL
                    )
                """)
                print(f"Deleted {cursor.rowcount} invalid references.")
            
    except OperationalError as e:
        print(f"Database error: {e}")

def main():
    print("Checking data integrity...\n")
    check_hinhanhdiadiem()
    print("\nData integrity check completed.")

if __name__ == "__main__":
    main()
