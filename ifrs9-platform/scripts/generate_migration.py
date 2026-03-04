#!/usr/bin/env python3
"""Generate Alembic migration for initial schema"""
import subprocess
import sys

def main():
    """Generate initial migration"""
    try:
        # Generate migration
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial schema with all tables"],
            cwd=".",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error generating migration: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        print("\nMigration generated successfully!")
        print("Review the migration file in alembic/versions/")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
