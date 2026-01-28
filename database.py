from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

# =========================================================
# 🔧 CONFIGURAÇÃO DO BANCO DE DADOS
# =========================================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =========================================================
# 👤 USUÁRIOS (SUPER ADMIN + CLIENTES)
# =========================================================
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_super_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ✅ RELACIONAMENTOS VALIDADOS
    bots = relationship("Bot", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

# =========================================================
# 🤖 BOTS
# =========================================================
class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bot_name = Column(String(100))
    telegram_token = Column(String(200), unique=True)
    pushinpay_token = Column(String(200), nullable=True)
    grupo_vip_id = Column(String(50), nullable=True)
    revenue_share_percent = Column(Float, default=10.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ✅ RELACIONAMENTOS VALIDADOS (incluindo remarketing_config)
    owner = relationship("User", back_populates="bots")
    planos = relationship("PlanoConfig", back_populates="bot")
    pedidos = relationship("Pedido", back_populates="bot")
    leads = relationship("Lead", back_populates="bot")
    fluxo = relationship("BotFlow", back_populates="bot", uselist=False)
    steps = relationship("BotFlowStep", back_populates="bot")
    order_bump = relationship("OrderBumpConfig", back_populates="bot", uselist=False)
    remarketing_campaigns = relationship("RemarketingCampaign", back_populates="bot")
    remarketing_config = relationship("RemarketingConfig", back_populates="bot", uselist=False)  # ⚠️ NOVO

# =========================================================
# 💲 PLANOS
# =========================================================
class PlanoConfig(Base):
    __tablename__ = "plano_config"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    nome_exibicao = Column(String(100))
    descricao = Column(Text)
    preco_atual = Column(Float)
    preco_original = Column(Float, nullable=True)  # ✅ VALIDADO
    preco_cheio = Column(Float, nullable=True)
    dias_duracao = Column(Integer, default=30)
    is_lifetime = Column(Boolean, default=False)  # ✅ VALIDADO
    key_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bot = relationship("Bot", back_populates="planos")

# =========================================================
# 🛒 PEDIDOS
# =========================================================
class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    telegram_id = Column(String(50))
    first_name = Column(String(100))
    username = Column(String(100), nullable=True)
    plano_nome = Column(String(100))
    plano_id = Column(Integer, nullable=True)
    valor = Column(Float)
    transaction_id = Column(String(100), unique=True)
    qr_code = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    tem_order_bump = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    tracking_id = Column(String(100), nullable=True)
    
    bot = relationship("Bot", back_populates="pedidos")

# =========================================================
# 👥 LEADS (CRM)
# =========================================================
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    user_id = Column(String(50))
    first_name = Column(String(100))
    username = Column(String(100), nullable=True)
    comprou = Column(Boolean, default=False)
    valor_gasto = Column(Float, default=0.0)
    ultima_interacao = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    tracking_id = Column(String(100), nullable=True)
    status = Column(String(20), default="active")  # ✅ VALIDADO
    
    bot = relationship("Bot", back_populates="leads")

# =========================================================
# 🎁 ORDER BUMP
# =========================================================
class OrderBumpConfig(Base):
    __tablename__ = "order_bump_config"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), unique=True)
    ativo = Column(Boolean, default=False)
    nome_produto = Column(String(100))
    preco = Column(Float)
    msg_texto = Column(Text)
    msg_media = Column(String, nullable=True)
    btn_aceitar = Column(String(50), default="✅ SIM, QUERO!")
    btn_recusar = Column(String(50), default="❌ Não, obrigado")
    autodestruir = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bot = relationship("Bot", back_populates="order_bump")

# =========================================================
# 📢 REMARKETING - CONFIGURAÇÕES GLOBAIS
# ⚠️ ESTA CLASSE É NOVA E CRÍTICA PARA O SISTEMA
# =========================================================
class RemarketingConfig(Base):
    """
    Configurações globais de remarketing por bot.
    Esta tabela armazena as preferências de envio automático
    e mensagens alternantes que são aplicadas a todas as campanhas.
    """
    __tablename__ = "remarketing_config"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), unique=True)
    
    # Configurações de Mensagens Alternantes
    alternating_enabled = Column(Boolean, default=False)
    alternating_messages = Column(JSON, default=list)  # Array de strings
    alternating_interval_hours = Column(Integer, default=24)
    
    # Configurações de Campanhas Automáticas
    auto_send_enabled = Column(Boolean, default=False)
    auto_send_delay_hours = Column(Integer, default=24)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bot = relationship("Bot", back_populates="remarketing_config")

# =========================================================
# 📢 REMARKETING - CAMPANHAS
# =========================================================
class RemarketingCampaign(Base):
    __tablename__ = "remarketing_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    campaign_id = Column(String, unique=True)
    
    # Configuração
    target = Column(String, default="todos")
    type = Column(String, default="massivo")
    config = Column(Text)
    
    # Status e Controle
    status = Column(String, default="agendado")
    is_enabled = Column(Boolean, default=True)  # ✅ VALIDADO
    
    # Agendamento
    dia_atual = Column(Integer, default=0)
    data_inicio = Column(DateTime, default=datetime.utcnow)
    proxima_execucao = Column(DateTime, nullable=True)
    
    # Oferta Promocional
    plano_id = Column(Integer, nullable=True)
    promo_price = Column(Float, nullable=True)
    expiration_at = Column(DateTime, nullable=True)
    
    # Métricas
    total_leads = Column(Integer, default=0)
    sent_success = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    data_envio = Column(DateTime, default=datetime.utcnow)
    
    bot = relationship("Bot", back_populates="remarketing_campaigns")
    
    # ✅ MÉTODOS AUXILIARES VALIDADOS
    def is_active(self) -> bool:
        """Verifica se a campanha está ativa e não expirada"""
        if not self.is_enabled:
            return False
        if self.expiration_at and datetime.utcnow() > self.expiration_at:
            return False
        return True
    
    def get_promo_price(self, plano: 'PlanoConfig') -> float:
        """Retorna o preço promocional ou preço padrão do plano"""
        if self.promo_price is not None and self.promo_price > 0:
            return self.promo_price
        return plano.preco_atual if plano else 0.0

# =========================================================
# 📊 REMARKETING - LOGS
# =========================================================
class RemarketingLog(Base):
    __tablename__ = "remarketing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    campaign_id = Column(String)
    user_id = Column(String)
    message_sent = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)

# =========================================================
# 🔄 MENSAGENS ALTERNANTES - CONTROLE DE ESTADO
# =========================================================
class AlternatingMessageState(Base):
    __tablename__ = "alternating_message_states"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    user_id = Column(String, nullable=False)
    last_message_index = Column(Integer, default=0)
    last_sent_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('bot_id', 'user_id', name='uix_bot_user_alternating'),
    )

# =========================================================
# 🔄 WEBHOOK RETRY SYSTEM
# =========================================================
class WebhookRetry(Base):
    """
    Rastreia webhooks que falharam e precisam ser reprocessados.
    Implementa exponential backoff automático.
    """
    __tablename__ = "webhook_retry"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_type = Column(String(50))
    payload = Column(Text)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    next_retry = Column(DateTime, nullable=True)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_error = Column(Text, nullable=True)
    reference_id = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<WebhookRetry(id={self.id}, type={self.webhook_type}, attempts={self.attempts}, status={self.status})>"

# =========================================================
# 💬 FLUXO (ESTRUTURA HÍBRIDA)
# =========================================================
class BotFlow(Base):
    __tablename__ = "bot_flows"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), unique=True)
    bot = relationship("Bot", back_populates="fluxo")
    
    start_mode = Column(String, default="padrao")
    miniapp_url = Column(String, nullable=True)
    miniapp_btn_text = Column(String, default="🛒 ABRIR LOJA")
    
    msg_boas_vindas = Column(Text, default="Olá! Bem-vindo(a)!")
    media_url = Column(String, nullable=True)
    btn_text_1 = Column(String, default="📋 Ver Planos")
    autodestruir_1 = Column(Boolean, default=False)
    mostrar_planos_1 = Column(Boolean, default=True)
    
    msg_2_texto = Column(Text, nullable=True)
    msg_2_media = Column(String, nullable=True)
    mostrar_planos_2 = Column(Boolean, default=False)

# =========================================================
# 🧩 TABELA DE PASSOS INTERMEDIÁRIOS
# =========================================================
class BotFlowStep(Base):
    __tablename__ = "bot_flow_steps"
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    step_order = Column(Integer, default=1)
    msg_texto = Column(Text, nullable=True)
    msg_media = Column(String, nullable=True)
    btn_texto = Column(String, default="Próximo ▶️")
    
    autodestruir = Column(Boolean, default=False)
    mostrar_botao = Column(Boolean, default=True)
    delay_seconds = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    bot = relationship("Bot", back_populates="steps")

# =========================================================
# 📝 AUDIT LOG
# =========================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100))
    resource_type = Column(String(50))
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")

# =========================================================
# 🔧 FUNÇÃO DE MIGRAÇÃO FORÇADA
# =========================================================
def forcar_atualizacao_tabelas():
    """
    Força a criação/atualização de colunas sem usar Alembic.
    Útil para adicionar colunas que faltam em produção.
    """
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    
    # Adicionar coluna is_lifetime se não existir
    if 'plano_config' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('plano_config')]
        if 'is_lifetime' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE plano_config ADD COLUMN is_lifetime BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("✅ Coluna 'is_lifetime' adicionada à tabela plano_config")
        if 'preco_original' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE plano_config ADD COLUMN preco_original FLOAT"))
                conn.commit()
                print("✅ Coluna 'preco_original' adicionada à tabela plano_config")
    
    # Adicionar coluna is_enabled se não existir
    if 'remarketing_campaigns' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('remarketing_campaigns')]
        if 'is_enabled' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE remarketing_campaigns ADD COLUMN is_enabled BOOLEAN DEFAULT TRUE"))
                conn.commit()
                print("✅ Coluna 'is_enabled' adicionada à tabela remarketing_campaigns")
    
    # Adicionar coluna status em leads se não existir
    if 'leads' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('leads')]
        if 'status' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE leads ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
                conn.commit()
                print("✅ Coluna 'status' adicionada à tabela leads")

# =========================================================
# 🚀 CRIAÇÃO DAS TABELAS
# =========================================================
def init_db():
    Base.metadata.create_all(bind=engine)
    forcar_atualizacao_tabelas()
    print("✅ Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_db()