# -*- coding: utf-8 -*-
"""
Terminal UI - Turkcell Fatura Asistanı
Butonlara tıklayarak API'yi test et
"""

import requests
import json
import os
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Colors:
    """Terminal renkleri"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Ekranı temizle"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Başlık yazdır"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("🚀 Turkcell Fatura Asistanı - Terminal UI")
    print("=" * 60)
    print(f"{Colors.ENDC}")

def print_menu():
    """Ana menüyü yazdır"""
    print(f"\n{Colors.OKCYAN}📋 ANA MENÜ{Colors.ENDC}")
    print("-" * 40)
    
    menu_items = [
        ("1", "👥 Kullanıcı İşlemleri"),
        ("2", "📊 Fatura İşlemleri"),
        ("3", "🔍 Analiz İşlemleri"),
        ("4", "🎯 What-If Simülasyonu"),
        ("5", "⭐ Bonus Özellikler"),
        ("6", "🧪 Test Tümü"),
        ("0", "❌ Çıkış")
    ]
    
    for key, label in menu_items:
        print(f"  {Colors.OKBLUE}{key}{Colors.ENDC} - {label}")
    
    print("-" * 40)

def print_submenu(title: str, items: list):
    """Alt menü yazdır"""
    print(f"\n{Colors.OKCYAN}{title}{Colors.ENDC}")
    print("-" * 40)
    
    for key, label in items:
        print(f"  {Colors.OKBLUE}{key}{Colors.ENDC} - {label}")
    
    print(f"  {Colors.OKBLUE}0{Colors.ENDC} - Geri Dön")
    print("-" * 40)

def get_user_input(prompt: str = "Seçiminiz: ") -> str:
    """Kullanıcı girişi al"""
    return input(f"{Colors.WARNING}{prompt}{Colors.ENDC}").strip()

def api_call(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """API çağrısı yap"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Server bağlantısı kurulamadı. Server çalışıyor mu?"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def print_result(result: Dict):
    """Sonucu yazdır"""
    if result["success"]:
        print(f"\n{Colors.OKGREEN}✅ Başarılı!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Response:{Colors.ENDC}")
        print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    else:
        print(f"\n{Colors.FAIL}❌ Hata: {result['error']}{Colors.ENDC}")

def wait_for_key():
    """Devam etmek için tuş bekle"""
    input(f"\n{Colors.WARNING}Devam etmek için Enter'a basın...{Colors.ENDC}")

def user_operations():
    """Kullanıcı işlemleri"""
    while True:
        clear_screen()
        print_header()
        
        items = [
            ("1", "👥 Tüm Kullanıcıları Listele"),
            ("2", "👤 Kullanıcı Detayı Getir"),
            ("3", "📋 Katalog Bilgileri")
        ]
        print_submenu("👥 KULLANICI İŞLEMLERİ", items)
        
        choice = get_user_input()
        
        if choice == "0":
            break
        elif choice == "1":
            print(f"\n{Colors.OKBLUE}👥 Tüm kullanıcılar getiriliyor...{Colors.ENDC}")
            result = api_call("/api/users")
            print_result(result)
            wait_for_key()
        elif choice == "2":
            user_id = get_user_input("Kullanıcı ID: ")
            print(f"\n{Colors.OKBLUE}👤 Kullanıcı {user_id} detayı getiriliyor...{Colors.ENDC}")
            result = api_call(f"/api/users/{user_id}")
            print_result(result)
            wait_for_key()
        elif choice == "3":
            print(f"\n{Colors.OKBLUE}📋 Katalog bilgileri getiriliyor...{Colors.ENDC}")
            result = api_call("/api/catalog")
            print_result(result)
            wait_for_key()

def bill_operations():
    """Fatura işlemleri"""
    while True:
        clear_screen()
        print_header()
        
        items = [
            ("1", "📊 Fatura Listesi"),
            ("2", "📝 Fatura Açıklama (LLM)")
        ]
        print_submenu("📊 FATURA İŞLEMLERİ", items)
        
        choice = get_user_input()
        
        if choice == "0":
            break
        elif choice == "1":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}📊 Fatura bilgileri getiriliyor...{Colors.ENDC}")
            result = api_call(f"/api/bills/{user_id}?period={period}")
            print_result(result)
            wait_for_key()
        elif choice == "2":
            bill_id = get_user_input("Fatura ID: ")
            print(f"\n{Colors.OKBLUE}📝 LLM ile fatura açıklaması yapılıyor...{Colors.ENDC}")
            result = api_call("/api/explain", "POST", {"bill_id": int(bill_id)})
            print_result(result)
            wait_for_key()

def analysis_operations():
    """Analiz işlemleri"""
    while True:
        clear_screen()
        print_header()
        
        items = [
            ("1", "🚨 Anomali Tespiti"),
            ("2", "👥 Kohort Kıyası"),
            ("3", "💰 Vergi Analizi")
        ]
        print_submenu("🔍 ANALİZ İŞLEMLERİ", items)
        
        choice = get_user_input()
        
        if choice == "0":
            break
        elif choice == "1":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}🚨 Anomaliler tespit ediliyor...{Colors.ENDC}")
            result = api_call("/api/anomalies", "POST", {"user_id": int(user_id), "period": period})
            print_result(result)
            wait_for_key()
        elif choice == "2":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            cohort_data = {
                "cohort_type": "retail",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
            print(f"\n{Colors.OKBLUE}👥 Kohort kıyası yapılıyor...{Colors.ENDC}")
            result = api_call("/api/cohort", "POST", {
                "user_id": int(user_id),
                "period": period,
                "cohort_data": cohort_data
            })
            print_result(result)
            wait_for_key()
        elif choice == "3":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}💰 Vergi analizi yapılıyor...{Colors.ENDC}")
            result = api_call("/api/tax-analysis", "POST", {"user_id": int(user_id), "period": period})
            print_result(result)
            wait_for_key()

def whatif_operations():
    """What-if simülasyonu"""
    while True:
        clear_screen()
        print_header()
        
        items = [
            ("1", "🎯 Tek Senaryo Simülasyonu"),
            ("2", "🏆 En İyi 3 Senaryo"),
            ("3", "🔧 Autofix Önerisi")
        ]
        print_submenu("🎯 WHAT-IF SİMÜLASYONU", items)
        
        choice = get_user_input()
        
        if choice == "0":
            break
        elif choice == "1":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            plan_id = get_user_input("Plan ID (opsiyonel): ")
            disable_vas = get_user_input("VAS devre dışı? (y/n): ").lower() == 'y'
            
            scenario = {"disable_vas": disable_vas}
            if plan_id:
                scenario["plan_id"] = int(plan_id)
            
            print(f"\n{Colors.OKBLUE}🎯 What-if simülasyonu çalıştırılıyor...{Colors.ENDC}")
            result = api_call("/api/whatif", "POST", {
                "user_id": int(user_id),
                "period": period,
                "scenario": scenario
            })
            print_result(result)
            wait_for_key()
        elif choice == "2":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}🏆 En iyi 3 senaryo bulunuyor...{Colors.ENDC}")
            result = api_call(f"/api/whatif/top3/{user_id}?period={period}")
            print_result(result)
            wait_for_key()
        elif choice == "3":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}🔧 Autofix önerisi oluşturuluyor...{Colors.ENDC}")
            result = api_call("/api/autofix", "POST", {"user_id": int(user_id), "period": period})
            print_result(result)
            wait_for_key()

def bonus_operations():
    """Bonus özellikler"""
    while True:
        clear_screen()
        print_header()
        
        items = [
            ("1", "👥 Kohort Kıyası"),
            ("2", "💰 Vergi Ayrıştırma"),
            ("3", "🔧 Autofix Önerisi"),
            ("4", "🛒 Mock Checkout")
        ]
        print_submenu("⭐ BONUS ÖZELLİKLER", items)
        
        choice = get_user_input()
        
        if choice == "0":
            break
        elif choice == "1":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            cohort_data = {
                "cohort_type": "retail",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
            print(f"\n{Colors.OKBLUE}👥 Kohort kıyası yapılıyor...{Colors.ENDC}")
            result = api_call("/api/cohort", "POST", {
                "user_id": int(user_id),
                "period": period,
                "cohort_data": cohort_data
            })
            print_result(result)
            wait_for_key()
        elif choice == "2":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}💰 Vergi analizi yapılıyor...{Colors.ENDC}")
            result = api_call("/api/tax-analysis", "POST", {"user_id": int(user_id), "period": period})
            print_result(result)
            wait_for_key()
        elif choice == "3":
            user_id = get_user_input("Kullanıcı ID: ")
            period = get_user_input("Dönem (YYYY-MM): ")
            print(f"\n{Colors.OKBLUE}🔧 Autofix önerisi oluşturuluyor...{Colors.ENDC}")
            result = api_call("/api/autofix", "POST", {"user_id": int(user_id), "period": period})
            print_result(result)
            wait_for_key()
        elif choice == "4":
            user_id = get_user_input("Kullanıcı ID: ")
            print(f"\n{Colors.OKBLUE}🛒 Mock checkout işlemi yapılıyor...{Colors.ENDC}")
            result = api_call("/api/checkout", "POST", {
                "user_id": int(user_id),
                "actions": [
                    {"type": "change_plan", "payload": {"plan_id": 3}},
                    {"type": "add_addon", "payload": {"addon_id": 101}}
                ]
            })
            print_result(result)
            wait_for_key()

def test_all():
    """Tüm endpoint'leri test et"""
    clear_screen()
    print_header()
    
    print(f"\n{Colors.OKBLUE}🧪 Tüm endpoint'ler test ediliyor...{Colors.ENDC}")
    
    tests = [
        ("Health Check", "/health", "GET"),
        ("Users List", "/api/users", "GET"),
        ("User Detail", "/api/users/1000", "GET"),
        ("Bills", "/api/bills/1001?period=2025-07", "GET"),
        ("Catalog", "/api/catalog", "GET"),
        ("Explain", "/api/explain", "POST", {"bill_id": 700101}),
        ("Anomalies", "/api/anomalies", "POST", {"user_id": 1001, "period": "2025-07"}),
        ("What-If", "/api/whatif", "POST", {"user_id": 1001, "period": "2025-07", "scenario": {"plan_id": 3}}),
        ("Top 3", "/api/whatif/top3/1001?period=2025-07", "GET"),
        ("Cohort", "/api/cohort", "POST", {"user_id": 1001, "period": "2025-07", "cohort_data": {"cohort_type": "retail", "avg_total": 180.25}}),
        ("Tax Analysis", "/api/tax-analysis", "POST", {"user_id": 1001, "period": "2025-07"}),
        ("Autofix", "/api/autofix", "POST", {"user_id": 1001, "period": "2025-07"}),
        ("Checkout", "/api/checkout", "POST", {"user_id": 1001, "actions": [{"type": "change_plan", "payload": {"plan_id": 3}}]})
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for i, (name, endpoint, method, *args) in enumerate(tests, 1):
        print(f"\n{Colors.OKCYAN}[{i}/{total_count}] {name}{Colors.ENDC}")
        
        if method == "GET":
            result = api_call(endpoint)
        else:
            result = api_call(endpoint, method, args[0])
        
        if result["success"]:
            print(f"{Colors.OKGREEN}✅ Başarılı{Colors.ENDC}")
            success_count += 1
        else:
            print(f"{Colors.FAIL}❌ Hata: {result['error']}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}📊 Test Sonuçları:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✅ Başarılı: {success_count}/{total_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ Başarısız: {total_count - success_count}/{total_count}{Colors.ENDC}")
    
    wait_for_key()

def main():
    """Ana fonksiyon"""
    while True:
        clear_screen()
        print_header()
        
        # Server kontrolü
        health_result = api_call("/health")
        if not health_result["success"]:
            print(f"{Colors.FAIL}❌ Server bağlantısı kurulamadı!{Colors.ENDC}")
            print(f"{Colors.WARNING}💡 Lütfen 'python api_server.py' komutunu çalıştırın.{Colors.ENDC}")
            wait_for_key()
            continue
        
        print(f"{Colors.OKGREEN}✅ Server bağlantısı kuruldu!{Colors.ENDC}")
        
        print_menu()
        choice = get_user_input()
        
        if choice == "0":
            print(f"\n{Colors.OKGREEN}👋 Görüşürüz!{Colors.ENDC}")
            break
        elif choice == "1":
            user_operations()
        elif choice == "2":
            bill_operations()
        elif choice == "3":
            analysis_operations()
        elif choice == "4":
            whatif_operations()
        elif choice == "5":
            bonus_operations()
        elif choice == "6":
            test_all()
        else:
            print(f"\n{Colors.FAIL}❌ Geçersiz seçim!{Colors.ENDC}")
            wait_for_key()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.OKGREEN}👋 Görüşürüz!{Colors.ENDC}")
        sys.exit(0)
