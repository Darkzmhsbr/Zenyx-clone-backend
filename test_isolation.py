"""
Script de teste para verificar isolamento de dados entre usuários.
Execute após implementar todas as proteções da Fase 2.
"""

import requests
import json

API_URL = "https://zenyx-gbs-testesv1-production.up.railway.app"

def test_isolation():
    print("🧪 INICIANDO TESTES DE ISOLAMENTO\n")
    
    # =========================================================
    # TESTE 1: Criar dois usuários diferentes
    # =========================================================
    print("📝 TESTE 1: Criando dois usuários...")
    
    user1_data = {
        "username": "user_test_1",
        "email": "user1@test.com",
        "password": "senha123",
        "full_name": "Usuário Teste 1"
    }
    
    user2_data = {
        "username": "user_test_2",
        "email": "user2@test.com",
        "password": "senha123",
        "full_name": "Usuário Teste 2"
    }
    
    # Registra usuário 1
    r1 = requests.post(f"{API_URL}/api/auth/register", json=user1_data)
    if r1.status_code == 200:
        token1 = r1.json()["access_token"]
        print(f"✅ Usuário 1 criado. Token: {token1[:20]}...")
    else:
        print(f"❌ Falha ao criar usuário 1: {r1.text}")
        # Tenta fazer login se já existe
        r1 = requests.post(f"{API_URL}/api/auth/login", json={
            "username": user1_data["username"],
            "password": user1_data["password"]
        })
        token1 = r1.json()["access_token"]
        print(f"✅ Login usuário 1. Token: {token1[:20]}...")
    
    # Registra usuário 2
    r2 = requests.post(f"{API_URL}/api/auth/register", json=user2_data)
    if r2.status_code == 200:
        token2 = r2.json()["access_token"]
        print(f"✅ Usuário 2 criado. Token: {token2[:20]}...")
    else:
        print(f"❌ Falha ao criar usuário 2: {r2.text}")
        # Tenta fazer login se já existe
        r2 = requests.post(f"{API_URL}/api/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = r2.json()["access_token"]
        print(f"✅ Login usuário 2. Token: {token2[:20]}...")
    
    # =========================================================
    # TESTE 2: Listar bots de cada usuário
    # =========================================================
    print("\n📋 TESTE 2: Listando bots de cada usuário...")
    
    # Usuário 1 lista seus bots
    headers1 = {"Authorization": f"Bearer {token1}"}
    bots1 = requests.get(f"{API_URL}/api/admin/bots", headers=headers1).json()
    print(f"   Usuário 1 vê {len(bots1)} bots")
    
    # Usuário 2 lista seus bots
    headers2 = {"Authorization": f"Bearer {token2}"}
    bots2 = requests.get(f"{API_URL}/api/admin/bots", headers=headers2).json()
    print(f"   Usuário 2 vê {len(bots2)} bots")
    
    # =========================================================
    # TESTE 3: Tentar acessar bot de outro usuário
    # =========================================================
    print("\n🔒 TESTE 3: Tentando acessar bot de outro usuário...")
    
    if bots1:
        bot_id_user1 = bots1[0]["id"]
        print(f"   Bot do Usuário 1: ID {bot_id_user1}")
        
        # Usuário 2 tenta acessar bot do Usuário 1
        r = requests.get(f"{API_URL}/api/admin/bots/{bot_id_user1}", headers=headers2)
        
        if r.status_code == 404:
            print("   ✅ ISOLAMENTO FUNCIONA! Usuário 2 não pode ver bot do Usuário 1")
        else:
            print(f"   ❌ FALHA DE SEGURANÇA! Usuário 2 conseguiu acessar bot do Usuário 1")
            print(f"   Resposta: {r.json()}")
    else:
        print("   ⚠️ Usuário 1 não tem bots para testar")
    
    # =========================================================
    # TESTE 4: Dashboard isolado
    # =========================================================
    print("\n📊 TESTE 4: Verificando isolamento no dashboard...")
    
    stats1 = requests.get(f"{API_URL}/api/admin/dashboard/stats", headers=headers1).json()
    stats2 = requests.get(f"{API_URL}/api/admin/dashboard/stats", headers=headers2).json()
    
    print(f"   Usuário 1 - Leads: {stats1.get('total_leads', 0)}")
    print(f"   Usuário 2 - Leads: {stats2.get('total_leads', 0)}")
    
    if stats1 != stats2:
        print("   ✅ Dashboards isolados corretamente")
    else:
        print("   ⚠️ Dashboards podem estar compartilhando dados")
    
    print("\n🎉 TESTES CONCLUÍDOS!")

if __name__ == "__main__":
    test_isolation()