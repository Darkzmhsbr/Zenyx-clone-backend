"""
🆕 MIGRAÇÃO FASE 3.3: AUDITORIA E LOGS
Cria a tabela audit_logs para rastreabilidade completa do sistema
"""

import os
from sqlalchemy import create_engine, inspect, text
from database import Base, AuditLog

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./sql_app.db"

def executar_migracao_audit_logs():
    """
    Cria a tabela audit_logs se ela ainda não existir
    """
    print("🔄 Iniciando Migração: Audit Logs (Fase 3.3)")
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Verifica se a tabela já existe
        if "audit_logs" in inspector.get_table_names():
            print("✅ Tabela 'audit_logs' já existe, pulando migração.")
            return
        
        # Cria apenas a tabela audit_logs
        print("📝 Criando tabela 'audit_logs'...")
        AuditLog.__table__.create(bind=engine)
        
        print("✅ Migração Fase 3.3 concluída com sucesso!")
        print("📊 Tabela 'audit_logs' criada:")
        print("   - user_id (FK para users)")
        print("   - username (denormalizado)")
        print("   - action (tipo de ação)")
        print("   - resource_type (tipo de recurso)")
        print("   - resource_id (ID do recurso)")
        print("   - description (descrição legível)")
        print("   - details (JSON com dados extras)")
        print("   - ip_address (IP do cliente)")
        print("   - user_agent (navegador/dispositivo)")
        print("   - success (bool)")
        print("   - error_message (se falhou)")
        print("   - created_at (timestamp)")
        
    except Exception as e:
        print(f"❌ Erro na migração Audit Logs: {e}")
        raise

if __name__ == "__main__":
    executar_migracao_audit_logs()