# -*- coding: utf-8 -*-
"""
Turkcell Fatura Asistanı - Modern GUI
CustomTkinter ile modern arayüz
"""

import customtkinter as ctk
import requests
import json
import threading
from typing import Dict, Any
import tkinter as tk
from tkinter import messagebox, scrolledtext

# CustomTkinter teması
ctk.set_appearance_mode("dark")  # dark, light, system
ctk.set_default_color_theme("blue")  # blue, green, dark-blue

BASE_URL = "http://localhost:8000"

class TurkcellGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🚀 Turkcell Fatura Asistanı")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Ana container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="🚀 Turkcell Fatura Asistanı", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)
        
        # Server durumu
        self.server_status = ctk.CTkLabel(
            self.main_frame,
            text="🔴 Server bağlantısı kontrol ediliyor...",
            font=ctk.CTkFont(size=14)
        )
        self.server_status.pack(pady=10)
        
        # Ana tab container
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab'ları oluştur
        self.create_tabs()
        
        # Server kontrolü
        self.check_server()
        
    def create_dashboard_tab(self):
        """Dashboard tab'ı - Mobil giriş gibi"""
        # Ana container
        main_container = ctk.CTkFrame(self.dashboard_tab)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title_frame = ctk.CTkFrame(main_container)
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame, 
            text="📱 Mobil Giriş - Fatura Asistanı", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Giriş alanı
        login_frame = ctk.CTkFrame(main_container)
        login_frame.pack(fill="x", pady=(0, 20))
        
        # User ID girişi
        input_frame = ctk.CTkFrame(login_frame)
        input_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            input_frame, 
            text="👤 Kullanıcı ID:", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))
        
        self.dashboard_user_var = ctk.StringVar(value="1001")
        user_entry = ctk.CTkEntry(
            input_frame, 
            textvariable=self.dashboard_user_var,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        user_entry.pack(pady=10)
        
        # Period seçimi
        period_frame = ctk.CTkFrame(input_frame)
        period_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(period_frame, text="📅 Dönem:").pack(side="left", padx=10)
        self.dashboard_period_var = ctk.StringVar(value="2025-07")
        period_combo = ctk.CTkComboBox(
            period_frame,
            values=["2025-05", "2025-06", "2025-07", "2025-08"],
            variable=self.dashboard_period_var,
            width=120
        )
        period_combo.pack(side="left", padx=10)
        
        # Giriş butonu
        login_button = ctk.CTkButton(
            input_frame,
            text="🚀 Fatura Bilgilerini Getir",
            command=self.load_dashboard_data,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        login_button.pack(pady=20)
        
        # Sonuç alanları
        results_frame = ctk.CTkFrame(main_container)
        results_frame.pack(fill="both", expand=True)
        
        # Sol panel - Özet bilgiler
        left_panel = ctk.CTkFrame(results_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            left_panel, 
            text="📊 Fatura Özeti", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.summary_text = ctk.CTkTextbox(left_panel, height=200)
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sağ panel - Detaylar
        right_panel = ctk.CTkFrame(results_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            right_panel, 
            text="🔍 Detaylı Analiz", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.details_text = ctk.CTkTextbox(right_panel, height=200)
        self.details_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Alt panel - Öneriler
        bottom_panel = ctk.CTkFrame(main_container)
        bottom_panel.pack(fill="x", pady=(20, 0))
        
        ctk.CTkLabel(
            bottom_panel, 
            text="💡 Tasarruf Önerileri", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.recommendations_text = ctk.CTkTextbox(bottom_panel, height=150)
        self.recommendations_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def create_tabs(self):
        """Tab'ları oluştur"""
        # Tab 1: Dashboard (Mobil Giriş)
        self.dashboard_tab = self.tabview.add("📱 Dashboard")
        self.create_dashboard_tab()
        
        # Tab 2: Kullanıcı İşlemleri
        self.user_tab = self.tabview.add("👥 Kullanıcılar")
        self.create_user_tab()
        
        # Tab 3: Fatura İşlemleri
        self.bill_tab = self.tabview.add("📊 Faturalar")
        self.create_bill_tab()
        
        # Tab 4: Analiz
        self.analysis_tab = self.tabview.add("🔍 Analiz")
        self.create_analysis_tab()
        
        # Tab 5: What-If
        self.whatif_tab = self.tabview.add("🎯 What-If")
        self.create_whatif_tab()
        
        # Tab 6: Bonus
        self.bonus_tab = self.tabview.add("⭐ Bonus")
        self.create_bonus_tab()
        
        # Tab 7: Test
        self.test_tab = self.tabview.add("🧪 Test")
        self.create_test_tab()
    
    def create_user_tab(self):
        """Kullanıcı tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.user_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Kullanıcı listesi
        ctk.CTkLabel(left_frame, text="👥 Kullanıcı Listesi", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Kullanıcı seçimi
        self.user_var = ctk.StringVar(value="1001")
        user_frame = ctk.CTkFrame(left_frame)
        user_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(user_frame, text="Kullanıcı ID:").pack(side="left", padx=5)
        self.user_entry = ctk.CTkEntry(user_frame, textvariable=self.user_var, width=100)
        self.user_entry.pack(side="left", padx=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="👥 Tüm Kullanıcılar", 
            command=self.get_all_users
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="👤 Kullanıcı Detayı", 
            command=self.get_user_detail
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="📋 Katalog", 
            command=self.get_catalog
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.user_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Sonuç", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.user_result = ctk.CTkTextbox(right_frame, height=400)
        self.user_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_bill_tab(self):
        """Fatura tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.bill_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="📊 Fatura İşlemleri", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Parametreler
        params_frame = ctk.CTkFrame(left_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # User ID
        user_frame = ctk.CTkFrame(params_frame)
        user_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(user_frame, text="Kullanıcı ID:").pack(side="left", padx=5)
        self.bill_user_var = ctk.StringVar(value="1001")
        ctk.CTkEntry(user_frame, textvariable=self.bill_user_var, width=100).pack(side="left", padx=5)
        
        # Period
        period_frame = ctk.CTkFrame(params_frame)
        period_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(period_frame, text="Dönem:").pack(side="left", padx=5)
        self.period_var = ctk.StringVar(value="2025-07")
        ctk.CTkEntry(period_frame, textvariable=self.period_var, width=100).pack(side="left", padx=5)
        
        # Bill ID
        bill_frame = ctk.CTkFrame(params_frame)
        bill_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(bill_frame, text="Fatura ID:").pack(side="left", padx=5)
        self.bill_id_var = ctk.StringVar(value="700101")
        ctk.CTkEntry(bill_frame, textvariable=self.bill_id_var, width=100).pack(side="left", padx=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="📊 Fatura Getir", 
            command=self.get_bill
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="📝 LLM Açıklama", 
            command=self.explain_bill
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.bill_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Sonuç", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.bill_result = ctk.CTkTextbox(right_frame, height=400)
        self.bill_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_analysis_tab(self):
        """Analiz tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.analysis_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="🔍 Analiz İşlemleri", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Parametreler
        params_frame = ctk.CTkFrame(left_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # User ID
        user_frame = ctk.CTkFrame(params_frame)
        user_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(user_frame, text="Kullanıcı ID:").pack(side="left", padx=5)
        self.analysis_user_var = ctk.StringVar(value="1001")
        ctk.CTkEntry(user_frame, textvariable=self.analysis_user_var, width=100).pack(side="left", padx=5)
        
        # Period
        period_frame = ctk.CTkFrame(params_frame)
        period_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(period_frame, text="Dönem:").pack(side="left", padx=5)
        self.analysis_period_var = ctk.StringVar(value="2025-07")
        ctk.CTkEntry(period_frame, textvariable=self.analysis_period_var, width=100).pack(side="left", padx=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="🚨 Anomali Tespiti", 
            command=self.detect_anomalies
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="👥 Kohort Kıyası", 
            command=self.cohort_analysis
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="💰 Vergi Analizi", 
            command=self.tax_analysis
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.analysis_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Sonuç", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.analysis_result = ctk.CTkTextbox(right_frame, height=400)
        self.analysis_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_whatif_tab(self):
        """What-if tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.whatif_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="🎯 What-If Simülasyonu", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Parametreler
        params_frame = ctk.CTkFrame(left_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # User ID
        user_frame = ctk.CTkFrame(params_frame)
        user_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(user_frame, text="Kullanıcı ID:").pack(side="left", padx=5)
        self.whatif_user_var = ctk.StringVar(value="1001")
        ctk.CTkEntry(user_frame, textvariable=self.whatif_user_var, width=100).pack(side="left", padx=5)
        
        # Period
        period_frame = ctk.CTkFrame(params_frame)
        period_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(period_frame, text="Dönem:").pack(side="left", padx=5)
        self.whatif_period_var = ctk.StringVar(value="2025-07")
        ctk.CTkEntry(period_frame, textvariable=self.whatif_period_var, width=100).pack(side="left", padx=5)
        
        # Plan ID
        plan_frame = ctk.CTkFrame(params_frame)
        plan_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(plan_frame, text="Plan ID:").pack(side="left", padx=5)
        self.plan_id_var = ctk.StringVar(value="3")
        ctk.CTkEntry(plan_frame, textvariable=self.plan_id_var, width=100).pack(side="left", padx=5)
        
        # VAS Checkbox
        self.disable_vas_var = ctk.BooleanVar(value=False)
        vas_checkbox = ctk.CTkCheckBox(
            params_frame, 
            text="VAS Devre Dışı", 
            variable=self.disable_vas_var
        )
        vas_checkbox.pack(pady=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="🎯 Tek Senaryo", 
            command=self.whatif_single
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="🏆 En İyi 3", 
            command=self.whatif_top3
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="🔧 Autofix", 
            command=self.autofix_recommendation
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.whatif_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Sonuç", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.whatif_result = ctk.CTkTextbox(right_frame, height=400)
        self.whatif_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_bonus_tab(self):
        """Bonus tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.bonus_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="⭐ Bonus Özellikler", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Parametreler
        params_frame = ctk.CTkFrame(left_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # User ID
        user_frame = ctk.CTkFrame(params_frame)
        user_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(user_frame, text="Kullanıcı ID:").pack(side="left", padx=5)
        self.bonus_user_var = ctk.StringVar(value="1001")
        ctk.CTkEntry(user_frame, textvariable=self.bonus_user_var, width=100).pack(side="left", padx=5)
        
        # Period
        period_frame = ctk.CTkFrame(params_frame)
        period_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(period_frame, text="Dönem:").pack(side="left", padx=5)
        self.bonus_period_var = ctk.StringVar(value="2025-07")
        ctk.CTkEntry(period_frame, textvariable=self.bonus_period_var, width=100).pack(side="left", padx=5)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="👥 Kohort Kıyası", 
            command=self.bonus_cohort
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="💰 Vergi Ayrıştırma", 
            command=self.bonus_tax
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="🔧 Autofix Önerisi", 
            command=self.bonus_autofix
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="🛒 Mock Checkout", 
            command=self.mock_checkout
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.bonus_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Sonuç", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.bonus_result = ctk.CTkTextbox(right_frame, height=400)
        self.bonus_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_test_tab(self):
        """Test tab'ı"""
        # Sol frame
        left_frame = ctk.CTkFrame(self.test_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text="🧪 Test İşlemleri", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="🧪 Tüm Endpoint'leri Test Et", 
            command=self.test_all_endpoints
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(
            button_frame, 
            text="🔍 Server Durumu", 
            command=self.check_server
        ).pack(fill="x", pady=2)
        
        # Sağ frame - Sonuç
        right_frame = ctk.CTkFrame(self.test_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text="📋 Test Sonuçları", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.test_result = ctk.CTkTextbox(right_frame, height=400)
        self.test_result.pack(fill="both", expand=True, padx=10, pady=10)
    
    def api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
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
    
    def update_result(self, textbox, result: Dict):
        """Sonucu textbox'a yazdır"""
        textbox.delete("1.0", "end")
        
        if result["success"]:
            textbox.insert("1.0", "✅ Başarılı!\n\n")
            textbox.insert("end", json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            textbox.insert("1.0", f"❌ Hata: {result['error']}\n")
    
    def check_server(self):
        """Server durumunu kontrol et"""
        def check():
            result = self.api_call("/health")
            if result["success"]:
                self.server_status.configure(text="🟢 Server bağlantısı kuruldu!", text_color="green")
            else:
                self.server_status.configure(text="🔴 Server bağlantısı kurulamadı!", text_color="red")
        
        threading.Thread(target=check, daemon=True).start()
    
    # Kullanıcı işlemleri
    def get_all_users(self):
        def call():
            result = self.api_call("/api/users")
            self.update_result(self.user_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def get_user_detail(self):
        def call():
            user_id = self.user_var.get()
            result = self.api_call(f"/api/users/{user_id}")
            self.update_result(self.user_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def get_catalog(self):
        def call():
            result = self.api_call("/api/catalog")
            self.update_result(self.user_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    # Fatura işlemleri
    def get_bill(self):
        def call():
            user_id = self.bill_user_var.get()
            period = self.period_var.get()
            result = self.api_call(f"/api/bills/{user_id}?period={period}")
            self.update_result(self.bill_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def explain_bill(self):
        def call():
            bill_id = self.bill_id_var.get()
            result = self.api_call("/api/explain", "POST", {"bill_id": int(bill_id)})
            self.update_result(self.bill_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    # Analiz işlemleri
    def detect_anomalies(self):
        def call():
            user_id = self.analysis_user_var.get()
            period = self.analysis_period_var.get()
            result = self.api_call("/api/anomalies", "POST", {"user_id": int(user_id), "period": period})
            self.update_result(self.analysis_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def cohort_analysis(self):
        def call():
            user_id = self.analysis_user_var.get()
            period = self.analysis_period_var.get()
            cohort_data = {
                "cohort_type": "retail",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
            result = self.api_call("/api/cohort", "POST", {
                "user_id": int(user_id),
                "period": period,
                "cohort_data": cohort_data
            })
            self.update_result(self.analysis_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def tax_analysis(self):
        def call():
            user_id = self.analysis_user_var.get()
            period = self.analysis_period_var.get()
            result = self.api_call("/api/tax-analysis", "POST", {"user_id": int(user_id), "period": period})
            self.update_result(self.analysis_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    # What-if işlemleri
    def whatif_single(self):
        def call():
            user_id = self.whatif_user_var.get()
            period = self.whatif_period_var.get()
            plan_id = self.plan_id_var.get()
            disable_vas = self.disable_vas_var.get()
            
            scenario = {"disable_vas": disable_vas}
            if plan_id:
                scenario["plan_id"] = int(plan_id)
            
            result = self.api_call("/api/whatif", "POST", {
                "user_id": int(user_id),
                "period": period,
                "scenario": scenario
            })
            self.update_result(self.whatif_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def whatif_top3(self):
        def call():
            user_id = self.whatif_user_var.get()
            period = self.whatif_period_var.get()
            result = self.api_call(f"/api/whatif/top3/{user_id}?period={period}")
            self.update_result(self.whatif_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def autofix_recommendation(self):
        def call():
            user_id = self.whatif_user_var.get()
            period = self.whatif_period_var.get()
            result = self.api_call("/api/autofix", "POST", {"user_id": int(user_id), "period": period})
            self.update_result(self.whatif_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    # Bonus işlemleri
    def bonus_cohort(self):
        def call():
            user_id = self.bonus_user_var.get()
            period = self.bonus_period_var.get()
            cohort_data = {
                "cohort_type": "retail",
                "avg_total": 180.25,
                "avg_data_gb": 12.5,
                "avg_minutes": 450,
                "avg_sms": 25,
                "percentile_25": 150.0,
                "percentile_75": 220.0
            }
            result = self.api_call("/api/cohort", "POST", {
                "user_id": int(user_id),
                "period": period,
                "cohort_data": cohort_data
            })
            self.update_result(self.bonus_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def bonus_tax(self):
        def call():
            user_id = self.bonus_user_var.get()
            period = self.bonus_period_var.get()
            result = self.api_call("/api/tax-analysis", "POST", {"user_id": int(user_id), "period": period})
            self.update_result(self.bonus_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def bonus_autofix(self):
        def call():
            user_id = self.bonus_user_var.get()
            period = self.bonus_period_var.get()
            result = self.api_call("/api/autofix", "POST", {"user_id": int(user_id), "period": period})
            self.update_result(self.bonus_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    def mock_checkout(self):
        def call():
            user_id = self.bonus_user_var.get()
            result = self.api_call("/api/checkout", "POST", {
                "user_id": int(user_id),
                "actions": [
                    {"type": "change_plan", "payload": {"plan_id": 3}},
                    {"type": "add_addon", "payload": {"addon_id": 101}}
                ]
            })
            self.update_result(self.bonus_result, result)
        
        threading.Thread(target=call, daemon=True).start()
    
    # Test işlemleri
    def test_all_endpoints(self):
        def call():
            self.test_result.delete("1.0", "end")
            self.test_result.insert("1.0", "🧪 Tüm endpoint'ler test ediliyor...\n\n")
            
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
                self.test_result.insert("end", f"[{i}/{total_count}] {name}\n")
                
                if method == "GET":
                    result = self.api_call(endpoint)
                else:
                    result = self.api_call(endpoint, method, args[0])
                
                if result["success"]:
                    self.test_result.insert("end", "✅ Başarılı\n")
                    success_count += 1
                else:
                    self.test_result.insert("end", f"❌ Hata: {result['error']}\n")
                
                self.test_result.see("end")
                self.root.update()
            
            self.test_result.insert("end", f"\n📊 Test Sonuçları:\n")
            self.test_result.insert("end", f"✅ Başarılı: {success_count}/{total_count}\n")
            self.test_result.insert("end", f"❌ Başarısız: {total_count - success_count}/{total_count}\n")
        
        threading.Thread(target=call, daemon=True).start()
    
    # Dashboard işlemleri
    def load_dashboard_data(self):
        """Dashboard için tüm verileri otomatik yükle"""
        def load():
            user_id = self.dashboard_user_var.get()
            period = self.dashboard_period_var.get()
            
            # Loading mesajı
            self.summary_text.delete("1.0", "end")
            self.details_text.delete("1.0", "end")
            self.recommendations_text.delete("1.0", "end")
            
            self.summary_text.insert("1.0", "🔄 Veriler yükleniyor...")
            self.details_text.insert("1.0", "🔄 Analiz yapılıyor...")
            self.recommendations_text.insert("1.0", "🔄 Öneriler hazırlanıyor...")
            
            try:
                # 1. Kullanıcı bilgileri
                user_result = self.api_call(f"/api/users/{user_id}")
                
                # 2. Fatura bilgileri
                bill_result = self.api_call(f"/api/bills/{user_id}?period={period}")
                
                # 3. LLM açıklaması (bill_id'yi bul)
                bill_id = None
                if bill_result["success"] and "bill" in bill_result["data"]:
                    bill_id = bill_result["data"]["bill"]["bill_id"]
                
                llm_result = None
                if bill_id:
                    llm_result = self.api_call("/api/explain", "POST", {"bill_id": int(bill_id)})
                
                # 4. Anomali analizi
                anomaly_result = self.api_call("/api/anomalies", "POST", {"user_id": int(user_id), "period": period})
                
                # 5. Kohort kıyası
                cohort_data = {
                    "cohort_type": "retail",
                    "avg_total": 180.25,
                    "avg_data_gb": 12.5,
                    "avg_minutes": 450,
                    "avg_sms": 25,
                    "percentile_25": 150.0,
                    "percentile_75": 220.0
                }
                cohort_result = self.api_call("/api/cohort", "POST", {
                    "user_id": int(user_id),
                    "period": period,
                    "cohort_data": cohort_data
                })
                
                # 6. Vergi analizi
                tax_result = self.api_call("/api/tax-analysis", "POST", {"user_id": int(user_id), "period": period})
                
                # 7. En iyi 3 senaryo
                top3_result = self.api_call(f"/api/whatif/top3/{user_id}?period={period}")
                
                # 8. Autofix önerisi
                autofix_result = self.api_call("/api/autofix", "POST", {"user_id": int(user_id), "period": period})
                
                # Sonuçları formatla ve göster
                self.update_dashboard_summary(user_result, bill_result, llm_result)
                self.update_dashboard_details(anomaly_result, cohort_result, tax_result)
                self.update_dashboard_recommendations(top3_result, autofix_result)
                
            except Exception as e:
                self.summary_text.delete("1.0", "end")
                self.summary_text.insert("1.0", f"❌ Hata: {str(e)}")
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_dashboard_summary(self, user_result, bill_result, llm_result):
        """Dashboard özet panelini güncelle"""
        self.summary_text.delete("1.0", "end")
        
        summary = "📊 FATURA ÖZETİ\n"
        summary += "=" * 40 + "\n\n"
        
        # Kullanıcı bilgileri
        if user_result["success"]:
            user_data = user_result["data"]
            summary += f"👤 Kullanıcı: {user_data.get('name', 'N/A')}\n"
            summary += f"📱 MSISDN: {user_data.get('msisdn', 'N/A')}\n"
            summary += f"🏷️ Tip: {user_data.get('type', 'N/A')}\n\n"
        
        # Fatura bilgileri
        if bill_result["success"]:
            bill_data = bill_result["data"]
            if "bill" in bill_data:
                bill = bill_data["bill"]
                summary += f"💰 Toplam: {bill.get('total_amount', 0)} TL\n"
                summary += f"📅 Dönem: {bill.get('period_start', 'N/A')} - {bill.get('period_end', 'N/A')}\n"
                summary += f"📋 Fatura ID: {bill.get('bill_id', 'N/A')}\n\n"
        
        # LLM açıklaması
        if llm_result and llm_result["success"]:
            llm_data = llm_result["data"]
            if "summary" in llm_data:
                summary += "🤖 AI Açıklaması:\n"
                summary += f"{llm_data['summary'].get('llm_summary', 'N/A')}\n"
        
        self.summary_text.insert("1.0", summary)
    
    def update_dashboard_details(self, anomaly_result, cohort_result, tax_result):
        """Dashboard detay panelini güncelle"""
        self.details_text.delete("1.0", "end")
        
        details = "🔍 DETAYLI ANALİZ\n"
        details += "=" * 40 + "\n\n"
        
        # Anomali analizi
        if anomaly_result["success"]:
            anomalies = anomaly_result["data"].get("anomalies", [])
            if anomalies:
                details += "🚨 ANOMALİLER:\n"
                for i, anomaly in enumerate(anomalies[:3], 1):  # İlk 3 anomali
                    details += f"{i}. {anomaly.get('category', 'N/A')}: {anomaly.get('reason', 'N/A')}\n"
                details += "\n"
        
        # Kohort kıyası
        if cohort_result["success"]:
            cohort_data = cohort_result["data"]
            details += "👥 KOHORT KIYASI:\n"
            details += f"• Ortalama: {cohort_data.get('cohort_average', 0)} TL\n"
            details += f"• Fark: {cohort_data.get('difference', 0)} TL\n"
            details += f"• Yüzde: %{cohort_data.get('difference_percent', 0)}\n"
            details += f"• Seviye: {cohort_data.get('percentile', 'N/A')}\n\n"
        
        # Vergi analizi
        if tax_result["success"]:
            tax_data = tax_result["data"]
            if "vergi_alloc" in tax_data:
                tax_alloc = tax_data["vergi_alloc"]
                details += "💰 VERGİ ANALİZİ:\n"
                details += f"• Net Tutar: {tax_alloc.get('net_total', 0)} TL\n"
                details += f"• KDV: {tax_alloc.get('taxes_total', 0)} TL\n"
                details += f"• KDV Oranı: %{tax_alloc.get('tax_rate', 0)}\n"
        
        self.details_text.insert("1.0", details)
    
    def update_dashboard_recommendations(self, top3_result, autofix_result):
        """Dashboard öneriler panelini güncelle"""
        self.recommendations_text.delete("1.0", "end")
        
        recommendations = "💡 TASARRUF ÖNERİLERİ\n"
        recommendations += "=" * 40 + "\n\n"
        
        # En iyi 3 senaryo
        if top3_result["success"]:
            scenarios = top3_result["data"].get("scenarios", [])
            if scenarios:
                recommendations += "🏆 EN İYİ 3 SENARYO:\n"
                for i, scenario in enumerate(scenarios[:3], 1):
                    saving = scenario.get("saving", 0)
                    recommendations += f"{i}. Tasarruf: {saving} TL\n"
                recommendations += "\n"
        
        # Autofix önerisi
        if autofix_result["success"]:
            autofix_data = autofix_result["data"]
            recommendations += "🔧 OTOMATİK ÖNERİ:\n"
            recommendations += f"• Potansiyel Tasarruf: {autofix_data.get('potential_saving', 0)} TL\n"
            recommendations += f"• Tasarruf Yüzdesi: %{autofix_data.get('saving_percent', 0)}\n"
            recommendations += f"• Gerekçe: {autofix_data.get('rationale', 'N/A')}\n"
        
        self.recommendations_text.insert("1.0", recommendations)
    
    def run(self):
        """Uygulamayı çalıştır"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TurkcellGUI()
    app.run()
