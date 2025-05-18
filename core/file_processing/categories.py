from pydantic import BaseModel, Field
from typing import List, Optional
import json
from pathlib import Path


class Subcategory(BaseModel):
    """Modelo para las subcategorías"""
    name: str


class Category(BaseModel):
    """Modelo para las categorías principales"""
    name: str
    subcategories: List[Subcategory]


class CategoriesData(BaseModel):
    """Modelo para el conjunto completo de datos de categorías"""
    categories: List[Category] = Field(default_factory=list)

    def __str__(self):
        return '- '+'\n- '.join([category.name for category in self.categories])

class CategoryLoader:
    """Cargador para leer y manipular los datos de categorías"""

    def __init__(self, file_path: Optional[str] = None):
        self.data: Optional[CategoriesData] = None
        if file_path:
            self.load_from_file(file_path)

    def load_from_file(self, file_path: str) -> CategoriesData:
        """Carga las categorías desde un archivo JSON"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe")

        if not path.suffix.lower() == '.json':
            raise ValueError(f"El archivo debe ser JSON, no {path.suffix}")

        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Convertimos la lista de categorías a nuestro modelo
        categories = [Category(**category) for category in raw_data]
        self.data = CategoriesData(categories=categories)
        return self.data

    def load_from_string(self, json_string: str) -> CategoriesData:
        """Carga las categorías desde una cadena JSON"""
        raw_data = json.loads(json_string)
        categories = [Category(**category) for category in raw_data]
        self.data = CategoriesData(categories=categories)
        return self.data

    def get_all_categories(self) -> List[Category]:
        """Retorna todas las categorías"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")
        return self.data.categories

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Busca una categoría por su ID"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")

        for category in self.data.categories:
            if category.id == category_id:
                return category
        return None

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Busca una categoría por su nombre (búsqueda exacta)"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")

        for category in self.data.categories:
            if category.name.lower() == name.lower():
                return category
        return None

    def search_categories(self, search_term: str) -> List[Category]:
        """Busca categorías que contengan el término en su nombre"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")

        search_term = search_term.lower()
        return [category for category in self.data.categories
                if search_term in category.name.lower()]

    def get_subcategory_by_id(self, subcategory_id: int) -> Optional[tuple[Category, Subcategory]]:
        """Busca una subcategoría por su ID y retorna la subcategoría junto con su categoría padre"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")

        for category in self.data.categories:
            for subcategory in category.subcategories:
                if subcategory.id == subcategory_id:
                    return (category, subcategory)
        return None

    def search_subcategories(self, search_term: str) -> List[tuple[Category, Subcategory]]:
        """Busca subcategorías que contengan el término en su nombre"""
        if not self.data:
            raise ValueError("Los datos no han sido cargados")

        search_term = search_term.lower()
        results = []

        for category in self.data.categories:
            for subcategory in category.subcategories:
                if search_term in subcategory.name.lower():
                    results.append((category, subcategory))

        return results

    def save_to_file(self, file_path: str) -> None:
        """Guarda los datos actuales en un archivo JSON"""
        if not self.data:
            raise ValueError("No hay datos para guardar")

        path = Path(file_path)

        # Convertir a formato compatible con JSON
        categories_data = [category.model_dump()
                           for category in self.data.categories]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, ensure_ascii=False, indent=2)
