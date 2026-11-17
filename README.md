# AhorraScan · backend

API del proyecto **AhorraScan**: una app móvil para escanear tickets de compra y
convertirlos en datos estructurados y categorizados.

## Qué hace

- **Autenticación** OAuth2 con JWT y passwords con hash (bcrypt/passlib).
- **Tickets**: alta, consulta y categorización de items, categorías y cuotas de uso.
- **Suscripciones** con Stripe: cobros, webhooks y control de cuotas por plan.
- **Clasificación con LLM**: el ticket (PDF → imagen) pasa por un grafo de
  **LangGraph** que clasifica cada producto con **Vertex AI** usando salidas
  estructuradas y fuzzy matching (Levenshtein) contra el catálogo.
- **Trazabilidad** con Langfuse de cada llamada al modelo.

## Stack

Python · FastAPI · SQLAlchemy 2 · LangGraph · Vertex AI · Stripe · Langfuse · Docker

## Desarrollo

```bash
docker compose up --build   # dependencias (Postgres, etc.)
uv run uvicorn main:app --reload
```

Las claves (Stripe, Vertex AI, Langfuse, base de datos) se leen del entorno; ver
`.env.example`.

> Nota: el repositorio conserva a la vez el monolito `_main.py` y el árbol
> refactorizado `api/` + `services/`, en plena migración.

MIT
