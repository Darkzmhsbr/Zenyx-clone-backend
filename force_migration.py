import os
import time
from sqlalchemy import create_engine, text

# Pega a URL do banco do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def forcar_atualizacao_tabelas():
    if not DATABASE_URL:
        print("❌ DATABASE_URL não encontrada.")
        return

    print("🚀 Iniciando Migração Forçada de Colunas...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Habilita o commit automático
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # =========================================================
        # 🆕 CRIAR TABELA USERS (SE NÃO EXISTIR)
        # =========================================================
        try:
            sql_create_users = text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR UNIQUE NOT NULL,
                    email VARCHAR UNIQUE NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    full_name VARCHAR,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_superuser BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute(sql_create_users)
            print("✅ Tabela 'users' verificada/criada")
        except Exception as e:
            print(f"⚠️ Erro ao criar tabela users: {e}")
        
        # =========================================================
        # 🆕 ADICIONAR COLUNA owner_id NA TABELA bots
        # =========================================================
        try:
            sql_add_owner = text("""
                ALTER TABLE bots 
                ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id);
            """)
            conn.execute(sql_add_owner)
            print("✅ Coluna 'owner_id' adicionada à tabela bots")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar owner_id: {e}")
        
        # =========================================================
        # COLUNAS EXISTENTES (MINIAPP CATEGORIES)
        # =========================================================
        novas_colunas = [
            "bg_color VARCHAR DEFAULT '#000000'",
            "banner_desk_url VARCHAR",
            "video_preview_url VARCHAR",
            "model_img_url VARCHAR",
            "model_name VARCHAR",
            "model_desc TEXT",
            "footer_banner_url VARCHAR",
            "deco_lines_url VARCHAR",
            "model_name_color VARCHAR DEFAULT '#ffffff'",
            "model_desc_color VARCHAR DEFAULT '#cccccc'"
        ]

        for coluna_sql in novas_colunas:
            col_name = coluna_sql.split()[0]
            try:
                sql = text(f"ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS {coluna_sql};")
                conn.execute(sql)
                print(f"✅ Coluna verificada/criada: {col_name}")
            except Exception as e:
                print(f"⚠️ Erro ao criar {col_name}: {e}")

    print("🎉 Migração Forçada Concluída!")

if __name__ == "__main__":
    forcar_atualizacao_tabelas()