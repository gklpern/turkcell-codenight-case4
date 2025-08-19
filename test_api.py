#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_api.py — API endpoint testleri
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Health check testi"""
    print("🔍 Health Check Testi")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Başarılı!")
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_users():
    """Kullanıcı endpoint testi"""
    print("\n👥 Kullanıcı Endpoint Testi")
    print("=" * 50)
    
    try:
        # Tüm kullanıcıları al
        response = requests.get(f"{BASE_URL}/api/users")
        print(f"Status: {response.status_code}")
        users = response.json()
        print(f"Kullanıcı sayısı: {len(users)}")
        print("✅ Başarılı!")
        
        # İlk kullanıcının detaylarını al
        if users:
            user_id = users[0]["user_id"]
            response = requests.get(f"{BASE_URL}/api/users/{user_id}")
            print(f"Kullanıcı {user_id} detayı: {response.json()}")
            print("✅ Başarılı!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_bills():
    """Fatura endpoint testi"""
    print("\n📊 Fatura Endpoint Testi")
    print("=" * 50)
    
    try:
        # Kullanıcı 1001'in faturalarını al
        user_id = 1001
        period = "2025-07"
        
        response = requests.get(f"{BASE_URL}/api/bills/{user_id}?period={period}")
        print(f"Status: {response.status_code}")
        bill = response.json()
        print(f"Fatura detayı: {json.dumps(bill, indent=2, ensure_ascii=False)}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_catalog():
    """Katalog endpoint testi"""
    print("\n📋 Katalog Endpoint Testi")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/catalog")
        print(f"Status: {response.status_code}")
        catalog = response.json()
        print(f"Plan sayısı: {len(catalog.get('plans', []))}")
        print(f"Addon sayısı: {len(catalog.get('addons', []))}")
        print(f"VAS sayısı: {len(catalog.get('vas', []))}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_explain():
    """Fatura açıklama testi"""
    print("\n📝 Fatura Açıklama Testi")
    print("=" * 50)
    
    try:
        payload = {"bill_id": 700101}
        response = requests.post(
            f"{BASE_URL}/api/explain",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"LLM Özeti: {result.get('llm_summary', 'N/A')}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_anomalies():
    """Anomali tespiti testi"""
    print("\n🚨 Anomali Tespiti Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "period": "2025-07"
        }
        response = requests.post(
            f"{BASE_URL}/api/anomalies",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Anomali sayısı: {len(result.get('anomalies', []))}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_whatif():
    """What-if simülasyonu testi"""
    print("\n🎯 What-If Simülasyonu Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "period": "2025-07",
            "scenario": {
                "plan_id": 3,
                "addons": [101],
                "disable_vas": True,
                "block_premium_sms": False
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/whatif",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Yeni toplam: {result.get('new_total', 'N/A')} TL")
        print(f"Tasarruf: {result.get('saving', 'N/A')} TL")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_top3_scenarios():
    """Top 3 senaryo testi"""
    print("\n🏆 Top 3 Senaryo Testi")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/whatif/top3/1001?period=2025-07")
        print(f"Status: {response.status_code}")
        result = response.json()
        scenarios = result.get('scenarios', [])
        print(f"Senaryo sayısı: {len(scenarios)}")
        for i, scenario in enumerate(scenarios[:3], 1):
            print(f"  {i}. Tasarruf: {scenario.get('saving', 'N/A')} TL")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_cohort_comparison():
    """Kohort kıyası testi"""
    print("\n👥 Kohort Kıyası Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "period": "2025-07",
            "cohort_data": {
                "cohort_type": "retail",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/cohort",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Kohort tipi: {result.get('cohort_type', 'N/A')}")
        print(f"Fark: {result.get('difference', 'N/A')} TL")
        print(f"Fark yüzdesi: %{result.get('difference_percent', 'N/A')}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_tax_analysis():
    """Vergi analizi testi"""
    print("\n💰 Vergi Analizi Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "period": "2025-07"
        }
        response = requests.post(
            f"{BASE_URL}/api/tax-analysis",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Anomali sayısı: {len(result.get('flags', []))}")
        print(f"Vergi toplamı: {result.get('vergi_alloc', {}).get('taxes_total', 'N/A')} TL")
        print(f"Birim maliyetler: {result.get('unit_costs', {})}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_autofix():
    """Autofix önerisi testi"""
    print("\n🔧 Autofix Önerisi Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "period": "2025-07"
        }
        response = requests.post(
            f"{BASE_URL}/api/autofix",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Potansiyel tasarruf: {result.get('potential_saving', 'N/A')} TL")
        print(f"Tasarruf yüzdesi: %{result.get('saving_percent', 'N/A')}")
        print(f"Gerekçe: {result.get('rationale', 'N/A')}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_checkout():
    """Checkout testi"""
    print("\n🛒 Checkout Testi")
    print("=" * 50)
    
    try:
        payload = {
            "user_id": 1001,
            "actions": [
                {
                    "type": "change_plan",
                    "payload": {"plan_id": 3}
                },
                {
                    "type": "add_addon",
                    "payload": {"addon_id": 101}
                }
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/checkout",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Order ID: {result.get('order_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print("✅ Başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🚀 Turkcell Fatura Asistanı - API Test")
    print("=" * 60)
    
    # Server'ın çalışıp çalışmadığını kontrol et
    print("🔍 Server kontrolü...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server çalışıyor!")
        else:
            print("❌ Server yanıt vermiyor")
            return
    except:
        print("❌ Server erişilemiyor. Lütfen server'ı başlatın:")
        print("   python api_server.py")
        return
    
    # Testleri çalıştır
    test_health()
    test_users()
    test_bills()
    test_catalog()
    test_explain()
    test_anomalies()
    test_whatif()
    test_top3_scenarios()
    test_cohort_comparison()
    test_tax_analysis()
    test_autofix()
    test_checkout()
    
    print("\n" + "=" * 60)
    print("🎉 Tüm testler tamamlandı!")
    print("=" * 60)

if __name__ == "__main__":
    main() 