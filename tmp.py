"""
Implementation script for updating the database schema and migrating category data.
This script should be run once to set up the new category structure.
"""
import argparse
import json
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Categoria, Item, Usuario, Ticket


def execute_sql_migration(sql_file_path):
    """Execute SQL migration script"""
    print(f"Executing SQL migration from {sql_file_path}")

    try:
        with open(sql_file_path, 'r') as f:
            sql_queries = f.read()

        # Split into individual statements
        statements = sql_queries.split(';')

        # Execute each statement
        with engine.connect() as connection:
            for statement in statements:
                if statement.strip():
                    try:
                        connection.execute(text(statement))
                        connection.commit()
                    except Exception as e:
                        print(f"Error executing statement: {statement}")
                        print(f"Error: {e}")
                        raise

        print("SQL migration completed successfully")
        return True

    except Exception as e:
        print(f"Error executing SQL migration: {e}")
        return False


def import_categories(json_file_path):
    """Import categories from JSON file"""
    print(f"Importing categories from {json_file_path}")

    try:
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)

        # Create session
        db = SessionLocal()
        try:
            # Dictionary to keep track of created categories by external_id
            category_map = {}

            # First pass: Create main categories
            for category in categories_data:
                main_category = Categoria(
                    nombre=category['name'],
                    nivel=0,  # Main category
                    activo=True
                )
                db.add(main_category)
                db.flush()  # Get ID without committing

                # Store in our map
                category_map[category['id']] = main_category.id

                # Second pass: Create subcategories for this main category
                for subcategory in category.get('subcategories', []):
                    sub = Categoria(
                        nombre=subcategory['name'],
                        parent_id=main_category.id,
                        nivel=1,  # Subcategory
                        activo=True
                    )
                    db.add(sub)
                    db.add(sub)

            # Commit all changes
            db.commit()

            print(
                f"Successfully imported {len(categories_data)} main categories and their subcategories")
            return True

        except Exception as e:
            db.rollback()
            print(f"Error importing categories: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        print(f"Error processing categories JSON: {e}")
        return False


def migrate_existing_items():
    """Migrate existing items to use the new category structure"""
    print("Migrating existing items to use the new category structure")

    db = SessionLocal()
    try:
        # Get all items
        items = db.query(Item).all()
        print(f"Found {len(items)} items to migrate")

        updated_count = 0
        for item in items:
            # Get category names from the item (already renamed by SQL migration)
            categoria_nombre = item.categoria_texto
            subcategoria_nombre = item.sub_categoria_texto

            if categoria_nombre:
                # Find main category
                categoria = db.query(Categoria).filter(
                    Categoria.nombre == categoria_nombre,
                    Categoria.nivel == 0
                ).first()

                if categoria:
                    item.categoria_id = categoria.id

                    # Find subcategory if it exists
                    if subcategoria_nombre:
                        subcategoria = db.query(Categoria).filter(
                            Categoria.nombre == subcategoria_nombre,
                            Categoria.parent_id == categoria.id,
                            Categoria.nivel == 1
                        ).first()

                        if subcategoria:
                            item.sub_categoria_id = subcategoria.id

                    updated_count += 1

        db.commit()
        print(
            f"Successfully updated {updated_count} items with category references")
        return True

    except Exception as e:
        db.rollback()
        print(f"Error migrating items: {str(e)}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Migrate database schema and import categories')
    parser.add_argument(
        '--sql', type=str, help='Path to SQL migration file', default='migration.sql')
    parser.add_argument('--categories', type=str,
                        help='Path to categories JSON file', default='categories.json')
    parser.add_argument('--skip-sql', action='store_true',
                        help='Skip SQL migration')
    parser.add_argument('--skip-import', action='store_true',
                        help='Skip category import')
    parser.add_argument('--skip-item-migration',
                        action='store_true', help='Skip migrating existing items')

    args = parser.parse_args()

    success = True

    # 1. Execute SQL migration
    if not args.skip_sql:
        if os.path.exists(args.sql):
            success = execute_sql_migration(args.sql) and success
        else:
            print(f"SQL file not found: {args.sql}")
            success = False

    # 2. Import categories
    if success and not args.skip_import:
        if os.path.exists(args.categories):
            success = import_categories(args.categories) and success
        else:
            print(f"Categories file not found: {args.categories}")
            success = False

    # 3. Migrate existing items
    if success and not args.skip_item_migration:
        success = migrate_existing_items() and success

    if success:
        print("Migration completed successfully!")
    else:
        print("Migration completed with errors. Please check the logs.")


if __name__ == "__main__":
    main()
