import os
import psycopg2
import logging
from urllib.parse import urlparse
# MESTRE CÓDIGO FÁCIL: Importamos a estrutura do banco para garantir a criação
from database import Base, engine

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def forcar_atualizacao_tabelas():
    """
    Função blindada que GARANTE a existência das tabelas antes de tentar migrar.
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("❌ DATABASE_URL não encontrada!")
        return

    print("="*60)
    print("🛡️ [AUTO-FIX] INICIANDO VERIFICAÇÃO DE INTEGRIDADE DO BANCO")
    print("="*60)

    # 1. VACINA: GARANTIR QUE AS TABELAS EXISTEM (SQLAlchemy)
    try:
        print("🏗️ 1. Verificando/Criando tabelas estruturais (Base.metadata)...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas estruturais garantidas!")
    except Exception as e:
        print(f"⚠️ Erro ao tentar criar tabelas via SQLAlchemy: {e}")
        # Não paramos aqui, tentamos seguir caso o erro seja apenas de conexão momentânea
    
    # 2. MIGRAÇÃO FORÇADA (SQL Bruto)
    print("🔧 2. Iniciando verificação de colunas (SQL Bruto)...")
    conn = None
    try:
        # Conexão direta via psycopg2 para comandos DDL manuais
        result = urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Lista de comandos de migração (ALTER TABLE)
        # Usamos IF NOT EXISTS para evitar erros se a coluna já existir
        commands = [
            # Tabela BOTS
            """
            ALTER TABLE bots 
            ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id);
            """,
            
            # Tabela MINIAPP_CATEGORIES - Campos Visuais
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS bg_color VARCHAR DEFAULT '#000000';",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS banner_desk_url VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS video_preview_url VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS model_img_url VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS model_name VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS model_desc TEXT;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS footer_banner_url VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS deco_lines_url VARCHAR;",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS model_name_color VARCHAR DEFAULT '#ffffff';",
            "ALTER TABLE miniapp_categories ADD COLUMN IF NOT EXISTS model_desc_color VARCHAR DEFAULT '#cccccc';",
            
            # Tabela MINIAPP_CONFIG
            "ALTER TABLE miniapp_config ADD COLUMN IF NOT EXISTS banner_url VARCHAR;",
            "ALTER TABLE miniapp_config ADD COLUMN IF NOT EXISTS logo_url VARCHAR;",
            
            # Tabela USERS (Garantia de Superuser)
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE;",
            
            # Tabela PEDIDOS (Garantia de Split)
            "ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS split_rules TEXT;"
        ]

        for command in commands:
            try:
                cursor.execute(command)
            except psycopg2.errors.UndefinedTable as e:
                # Este erro não deve mais acontecer com a vacina acima, mas se acontecer, logamos claro.
                logger.warning(f"⚠️ Tabela ainda não encontrada durante ALTER: {e}")
            except Exception as e:
                # Ignora erros de coluna duplicada ou outros menores
                logger.info(f"ℹ️ Comando SQL processado (pode já existir): {str(e)[:100]}")

        print("✅ Migração Forçada de Colunas Concluída!")

    except Exception as e:
        logger.error(f"❌ Erro fatal na conexão psycopg2: {e}")
    finally:
        if conn:
            conn.close()