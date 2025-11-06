from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexión para PostgreSQL. (Asegúrate que la BD "imc_db" exista)
DATABASE_URL = "postgresql://admin:postgres@localhost/imc_db"

# --- Opcional: Para usar SQLite (base de datos interna) ---
# DATABASE_URL = "sqlite:///./test.db"
# -----------------------------------------------------------

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()