"""
Script to reset the database and create fresh migrations.
"""
import os
import shutil
import sys

def reset_database():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(base_dir, 'vivu_backend')
    
    # Add the project directory to the Python path
    sys.path.append(backend_dir)
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
    import django
    django.setup()
    
    # Get database path from settings
    from django.conf import settings
    db_path = settings.DATABASES['default']['NAME']
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except PermissionError as e:
            print(f"Error removing database: {e}")
            print("Please make sure no other processes are using the database.")
            return
    
    # Remove migration files
    for app in ['places', 'users', 'itineraries']:
        migrations_dir = os.path.join(backend_dir, 'apps', app, 'migrations')
        if os.path.exists(migrations_dir):
            for filename in os.listdir(migrations_dir):
                if filename != '__init__.py' and filename.endswith('.py'):
                    file_path = os.path.join(migrations_dir, filename)
                    try:
                        os.remove(file_path)
                        print(f"Removed migration: {file_path}")
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")
    
    # Create __init__.py in migrations directories if they don't exist
    for app in ['places', 'users', 'itineraries']:
        migrations_dir = os.path.join(backend_dir, 'apps', app, 'migrations')
        os.makedirs(migrations_dir, exist_ok=True)
        init_file = os.path.join(migrations_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# This file is required for Python to treat the directory as a package')
    
    print("\nCreating fresh migrations...")
    
    # Create and apply migrations
    os.chdir(backend_dir)
    os.system('python manage.py makemigrations')
    os.system('python manage.py migrate')
    
    print("\nDatabase reset complete!")

if __name__ == "__main__":
    reset_database()
