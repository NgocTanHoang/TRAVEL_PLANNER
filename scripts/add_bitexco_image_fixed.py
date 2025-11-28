import sqlite3
from datetime import datetime
from pathlib import Path

def find_bitexco_skydeck(db_path):
    """Find the Bitexco Skydeck record in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Search for Bitexco Skydeck record
    cursor.execute("""
        SELECT maDiaDiem, tenDiaDiem, maTinhThanh 
        FROM DIADIEM 
        WHERE tenDiaDiem LIKE '%Bitexco%' OR tenDiaDiem LIKE '%Skydeck%';
    """)
    
    result = cursor.fetchone()
    conn.close()
    return result

def add_image_to_place(db_path, place_id, image_url):
    """Add an image URL to the HINHANHDIADIEM table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the image already exists for this place
        cursor.execute(
            "SELECT COUNT(*) FROM HINHANHDIADIEM WHERE maDiaDiem = ? AND urlHinhAnh = ?",
            (place_id, image_url)
        )
        if cursor.fetchone()[0] > 0:
            return False, "Image already exists for this place"
        
        # Get the next available maHinhAnh
        cursor.execute("SELECT COALESCE(MAX(maHinhAnh), 0) + 1 FROM HINHANHDIADIEM")
        next_id = cursor.fetchone()[0] or 1
        
        # Insert the new image
        cursor.execute("""
            INSERT INTO HINHANHDIADIEM 
            (maHinhAnh, maDiaDiem, urlHinhAnh, moTa, laChinh, ngayTao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            next_id, 
            place_id, 
            image_url, 
            "Bitexco Skydeck - Ảnh chụp từ tầng quan sát", 
            1,  # laChinh = True (main image)
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        conn.commit()
        return True, f"Successfully added image (ID: {next_id}) to place ID {place_id}"
        
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = r"D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend\db.sqlite3"
    image_url = "https://bitexco.com.vn/wp-content/uploads/2024/12/348231198_660338669252219_9098741285648254994_n.jpg"
    
    print(f"Searching for Bitexco Skydeck in database...")
    place = find_bitexco_skydeck(db_path)
    
    if not place:
        print("Bitexco Skydeck not found in the database.")
    else:
        place_id, place_name, province_id = place
        print(f"Found: {place_name} (ID: {place_id}, Province ID: {province_id})")
        
        print("\nAdding image to the database...")
        success, message = add_image_to_place(db_path, place_id, image_url)
        
        if success:
            print(f"[SUCCESS] {message}")
            print(f"Image URL: {image_url}")
        else:
            print(f"[X] Failed to add image: {message}")
