# =========================================================
# 🔄 MIGRAÇÃO V7 - CANAL DE DESTINO POR PLANO
# =========================================================

import os
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

def executar_migracao_v7():
    """
    Adiciona a coluna 'id_canal_destino' na tabela planos_config.
    Isso permite que um plano específico leve para um canal diferente do padrão do bot.
    """
    try:
        # Pega a URL do ambiente ou usa sqlite local como fallback
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
        # Ajuste para Railway (postgres:// -> postgresql://)
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

        engine = create_engine(DATABASE_URL)
        
        logger.info("🔄 [MIGRAÇÃO V7] Verificando coluna id_canal_destino em planos_config...")
        
        with engine.connect() as conn:
            # Adiciona coluna 'id_canal_destino' (VARCHAR/String)
            # Padrão é NULL (significa: use o canal do bot)
            sql_coluna = """
            ALTER TABLE planos_config 
            ADD COLUMN IF NOT EXISTS id_canal_destino VARCHAR;
            """
            conn.execute(text(sql_coluna))
            conn.commit()
            logger.info("   ✅ Coluna 'id_canal_destino' verificada/adicionada com sucesso!")
            
            return True
            
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("ℹ️  [MIGRAÇÃO V7] Coluna já existe.")
            return True
        else:
            logger.error(f"❌ Erro na Migração V7: {e}")
            return False