import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import User, Bot

# Pega a URL do banco do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def atribuir_bots_ao_primeiro_usuario():
    """
    Atribui todos os bots sem dono (owner_id = NULL) ao primeiro usuário criado.
    Isso deve ser executado UMA ÚNICA VEZ após implementar o sistema de autenticação.
    """
    if not DATABASE_URL:
        print("❌ DATABASE_URL não encontrada.")
        return

    print("🚀 Iniciando atribuição de bots existentes...")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Busca o primeiro usuário (geralmente o admin/criador do sistema)
        primeiro_usuario = db.query(User).order_by(User.id).first()
        
        if not primeiro_usuario:
            print("⚠️ Nenhum usuário encontrado! Crie um usuário primeiro via /register")
            return
        
        print(f"👤 Primeiro usuário encontrado: {primeiro_usuario.username} (ID: {primeiro_usuario.id})")
        
        # 2. Busca todos os bots sem dono (owner_id NULL)
        bots_orfaos = db.query(Bot).filter(Bot.owner_id == None).all()
        
        if not bots_orfaos:
            print("✅ Nenhum bot órfão encontrado. Todos os bots já têm dono!")
            return
        
        print(f"📦 Encontrados {len(bots_orfaos)} bots sem dono:")
        for bot in bots_orfaos:
            print(f"   - {bot.nome} (ID: {bot.id})")
        
        # 3. Atribui todos os bots órfãos ao primeiro usuário
        for bot in bots_orfaos:
            bot.owner_id = primeiro_usuario.id
            print(f"   ✅ {bot.nome} → atribuído a {primeiro_usuario.username}")
        
        db.commit()
        
        print(f"\n🎉 Migração concluída! {len(bots_orfaos)} bots atribuídos a {primeiro_usuario.username}")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    atribuir_bots_ao_primeiro_usuario()