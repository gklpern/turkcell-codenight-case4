#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_test.py — LLM entegrasyonu test dosyası
"""

import os
import json
from general_scripts.llm_client import call_llm, render_bill_summary_llm
from general_scripts.cohort_analysis import analyze_cohort_comparison
from general_scripts.tax_analysis import analyze_tax_breakdown
from general_scripts.autofix_engine import generate_autofix_recommendation

def test_basic_llm():
    """Temel LLM çağrısı testi"""
    print("🔍 Temel LLM Testi")
    print("=" * 50)
    
    prompt = "Merhaba! Sen bir fatura asistanısın. Kısaca kendini tanıt."
    print(f"Prompt: {prompt}")
    print("-" * 40)
    
    try:
        response = call_llm(prompt)
        print(f"Response: {response}")
        print(f"✅ Başarılı! Response uzunluğu: {len(response)} karakter")
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("💡 OpenAI API Key'inizi kontrol edin:")
        print("   export OPENAI_API_KEY=sk-...")

def test_bill_summary():
    """Fatura özeti testi"""
    print("\n📊 Fatura Özeti Testi")
    print("=" * 50)
    
    # Mock fatura verisi
    mock_payload = {
        "summary": {
            "period": "2025-07",
            "total": 245.5,
            "taxes": 37.5,
            "usage_summary": {
                "gb": 8.5,
                "minutes": 320,
                "sms": 45,
                "roaming_gb": 0.2
            },
            "baseline_total_mean": 180.25,
            "total_delta": 65.25
        },
        "breakdown": [
            {
                "category": "one_off",
                "total": 180.0,
                "lines": [{"text": "Aylık sabit ücret", "amount": 180.0}]
            },
            {
                "category": "premium_sms",
                "total": 58.0,
                "lines": [{"text": "Premium SMS", "amount": 58.0}]
            }
        ],
        "contributors": [
            {
                "category": "premium_sms",
                "current": 58.0,
                "baseline_mean": 12.0,
                "delta": 46.0
            }
        ]
    }
    
    print("Mock fatura verisi:")
    print(json.dumps(mock_payload, indent=2, ensure_ascii=False))
    print("-" * 40)
    
    try:
        summary = render_bill_summary_llm(mock_payload)
        print(f"LLM Özeti: {summary}")
        print(f"✅ Başarılı! Özet uzunluğu: {len(summary)} karakter")
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_different_scenarios():
    """Farklı senaryolar testi"""
    print("\n🎯 Farklı Senaryolar Testi")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Yüksek Premium SMS",
            "payload": {
                "summary": {
                    "period": "2025-07",
                    "total": 350.0,
                    "taxes": 53.5,
                    "usage_summary": {"gb": 10.0, "minutes": 400, "sms": 80, "roaming_gb": 0.0},
                    "baseline_total_mean": 200.0,
                    "total_delta": 150.0
                },
                "contributors": [{"category": "premium_sms", "current": 150.0, "baseline_mean": 20.0, "delta": 130.0}]
            }
        },
        {
            "name": "Roaming Kullanımı",
            "payload": {
                "summary": {
                    "period": "2025-07",
                    "total": 420.0,
                    "taxes": 64.0,
                    "usage_summary": {"gb": 15.0, "minutes": 600, "sms": 30, "roaming_gb": 2.5},
                    "baseline_total_mean": 180.0,
                    "total_delta": 240.0
                },
                "contributors": [{"category": "roaming", "current": 180.0, "baseline_mean": 0.0, "delta": 180.0}]
            }
        },
        {
            "name": "Normal Kullanım",
            "payload": {
                "summary": {
                    "period": "2025-07",
                    "total": 185.0,
                    "taxes": 28.0,
                    "usage_summary": {"gb": 5.0, "minutes": 200, "sms": 15, "roaming_gb": 0.0},
                    "baseline_total_mean": 190.0,
                    "total_delta": -5.0
                },
                "contributors": [{"category": "voice", "current": 25.0, "baseline_mean": 15.0, "delta": 10.0}]
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Senaryo {i}: {scenario['name']}")
        print("-" * 40)
        
        try:
            summary = render_bill_summary_llm(scenario['payload'])
            print(f"Özet: {summary}")
            print("✅ Başarılı")
        except Exception as e:
            print(f"❌ Hata: {e}")

def test_cohort_comparison():
    """Kohort kıyası testi"""
    print("\n👥 Kohort Kıyası Testi")
    print("=" * 50)
    
    mock_payload = {
        "summary": {
            "total": 245.5,
            "usage_summary": {"gb": 8.5, "minutes": 320, "sms": 45}
        }
    }
    
    mock_cohort_data = {
        "cohort_type": "retail",
        "avg_total": 180.25,
        "avg_data_gb": 12.5,
        "avg_minutes": 450,
        "avg_sms": 25,
        "percentile_25": 150.0,
        "percentile_75": 220.0
    }
    
    try:
        analysis = analyze_cohort_comparison(mock_payload, mock_cohort_data)
        print("Kohort Analizi:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("✅ Başarılı!")
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_tax_breakdown():
    """Vergi ayrıştırma testi"""
    print("\n💰 Vergi Ayrıştırma Testi")
    print("=" * 50)
    
    mock_payload = {
        "summary": {
            "total": 245.5,
            "taxes": 37.5,
            "usage_summary": {"gb": 8.5, "minutes": 320, "sms": 45}
        },
        "breakdown": [
            {"category": "one_off", "total": 180.0},
            {"category": "premium_sms", "total": 58.0},
            {"category": "vas", "total": 24.9}
        ]
    }
    
    try:
        analysis = analyze_tax_breakdown(mock_payload)
        print("Vergi Analizi:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("✅ Başarılı!")
    except Exception as e:
        print(f"❌ Hata: {e}")

def test_autofix_recommendation():
    """Autofix önerisi testi"""
    print("\n🔧 Autofix Önerisi Testi")
    print("=" * 50)
    
    mock_payload = {
        "summary": {"total": 245.5}
    }
    
    mock_scenarios = [
        {
            "new_total": 180.0,
            "saving": 65.5,
            "plan_id": 3,
            "addons": [101, 103],
            "disable_vas": True,
            "block_premium_sms": False,
            "details": {"fixed_fee": 529.0, "addons_cost": 88.0}
        },
        {
            "new_total": 200.0,
            "saving": 45.5,
            "plan_id": 2,
            "addons": [101],
            "disable_vas": False,
            "block_premium_sms": True,
            "details": {"fixed_fee": 429.0, "addons_cost": 79.0}
        }
    ]
    
    try:
        recommendation = generate_autofix_recommendation(mock_payload, mock_scenarios)
        print("Autofix Önerisi:")
        print(json.dumps(recommendation, indent=2, ensure_ascii=False))
        print("✅ Başarılı!")
    except Exception as e:
        print(f"❌ Hata: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🚀 Turkcell Fatura Asistanı - LLM Test")
    print("OpenAI ChatGPT ile fatura özeti testi")
    print("=" * 60)
    
    # API Key kontrolü
    print("\n🔑 API Key Kontrolü")
    print("=" * 50)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ API Key bulundu: {api_key[:10]}...{api_key[-10:]}")
        print(f"📋 Model: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
        print(f"🌐 Base URL: {os.getenv('OPENAI_BASE', 'https://api.openai.com')}")
    else:
        print("❌ OPENAI_API_KEY bulunamadı!")
        print("💡 Lütfen API key'inizi ayarlayın:")
        print("   export OPENAI_API_KEY=sk-...")
        print("   veya")
        print("   set OPENAI_API_KEY=sk-... (Windows)")
    
    # Testleri çalıştır
    test_basic_llm()
    test_bill_summary()
    test_different_scenarios()
    test_cohort_comparison()
    test_tax_breakdown()
    test_autofix_recommendation()
    
    print("\n" + "=" * 60)
    print("🎉 Test tamamlandı!")
    print("=" * 60)

if __name__ == "__main__":
    main()
