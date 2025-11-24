import streamlit as st 
import google.generativeai as genai
import os
from PyPDF2 import PdfReader
import json
import random
import pandas as pd  # Stok listesi için

# -----------------------------------------------------------------------------
# 1. AYARLAR VE STİL (DARK MEDICAL PRO) – V8.1
# -----------------------------------------------------------------------------
st.set_page_config(page_title="MDR Uzmanlık Akademisi v8.1", layout="wide", page_icon="🎓")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    .header-box {
        padding: 25px;
        background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        border: 1px solid #4CAF50;
    }

    .info-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 15px;
    }

    .stButton>button {
        background-color: #00adb5;
        color: white;
        border-radius: 6px;
        border: none;
    }

    .stButton>button:hover {
        background-color: #008c93;
    }

    .stChatMessage {
        background-color: #262730;
        border: 1px solid #30363d;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. V2.0 – EĞİTİM MODÜLÜ İÇERİKLERİ (STATİK DERS NOTLARI + MINI QUIZ)
# -----------------------------------------------------------------------------
LESSONS = {
    "Giriş & Tanımlar": {
        "summary": """
MDR 2017/745, AB'deki tıbbi cihazların piyasaya arzı, piyasada bulundurulması ve kullanımına ilişkin temel yasal çerçeveyi tanımlar. Bu modülde MDR kapsamı, cihaz tanımı, aksesuar, ekonomik operatörler ve "intended purpose" (amaçlanan kullanım) kavramları ele alınır.
""",
        "sections": [
            {
                "title": "1. MDR'nin Amacı ve Kapsamı",
                "body": """
MDR'nin temel amacı, tıbbi cihazların güvenli ve performanslı olmasını sağlamak, aynı zamanda yenilikçi ürünlerin pazara girişini engellemeden yüksek bir hasta güvenliği standardı korumaktır.

- MDD'den (93/42/EEC) MDR'ye geçiş ile birlikte klinik kanıt, izlenebilirlik ve post-market gözetim gereklilikleri önemli ölçüde sıkılaştırılmıştır.
- MDR kapsamına giren ürün yelpazesi genişlemiştir (örneğin estetik amaçlı bazı ürünler de dahil edilmiştir).
"""
            },
            {
                "title": "2. Tıbbi Cihaz Tanımı",
                "body": """
Bir tıbbi cihaz, üretici tarafından özel olarak **tıbbi amaçlar** için tasarlanmış ve insan üzerinde kullanılan her türlü cihaz, aygıt, yazılım, implant, reaktif vb. ürün olarak tanımlanır.

Ana kriterler:
- İnsan üzerinde kullanılır.
- Temel amaç tıbbi bir amaçtır (teşhis, izleme, tedavi, hafifletme vb.).
- Farmakolojik, immünolojik veya metabolik bir etki **birincil** etki mekanizması değildir, ancak yardımcı rol oynayabilir.
"""
            },
            {
                "title": "3. Aksesuar ve Complementary Products",
                "body": """
Aksesuar, tıbbi cihazın kendisi olmamakla birlikte, cihazın **amacına uygun şekilde kullanılmasını** mümkün kılan veya destekleyen üründür (örneğin bir cerrahi sistemin özel adaptör aparatı).

Complementary product ise genellikle MDR kapsamı dışında kalan, ancak tıbbi cihazla birlikte kullanılan (örneğin bazı yazılım veya genel amaçlı enjektörler) ürünler olabilir. Buradaki ayrım, regülasyon kapsamını ve sorumlulukları doğrudan etkiler.
"""
            },
            {
                "title": "4. Ekonomik Operatörler",
                "body": """
MDR, dört ana ekonomik operatör tanımlar:
- Üretici (Manufacturer)
- Yetkili Temsilci (Authorised Representative)
- İthalatçı (Importer)
- Dağıtıcı (Distributor)

Her birinin ayrı ayrı sorumlulukları vardır; örneğin üretici teknik dosyadan sorumluyken, ithalatçı AB pazarına girişte uygunluk beyanı ve etiketleme gibi konularda doğrulama yapmakla yükümlüdür.
"""
            },
            {
                "title": "5. Intended Purpose (Amaçlanan Kullanım)",
                "body": """
Cihazın sınıflandırması, klinik değerlendirme kapsamı ve risk analizi, üreticinin belirlediği 'intended purpose' üzerine kuruludur. Bu ifade, kullanma talimatı, etiketleme ve pazarlama dokümanlarında açıkça belirtilmelidir.

Eksik veya muğlak bir intended purpose ifadesi:
- Yanlış risk sınıfı,
- Eksik klinik kanıt,
- Uygun olmayan GSPR karşılaması gibi ciddi uygunsuzluklara yol açabilir.
"""
            },
        ],
        "key_points": [
            "MDR, MDD'ye göre çok daha kapsamlı ve risk odaklıdır.",
            "Tıbbi cihaz tanımı ve intended purpose, regülasyonun merkezindedir.",
            "Ekonomik operatörlerin rol ve sorumlulukları net bir şekilde ayrılmıştır.",
            "Aksesuarlar da MDR kapsamında cihaz gibi değerlendirilir.",
        ],
        "refs": [
            "MDR 2017/745 Madde 2 (Tanımlar)",
            "MDR 2017/745 Madde 5 (Piyasaya arz ve hizmete sunma koşulları)"
        ],
        "examples": [
            "Sadece hasta vücut sıcaklığını ölçen dijital termometre → tıbbi cihaz.",
            "Fitness amacıyla kullanılan, sadece wellness verisi gösteren bileklik → tipik olarak MDR kapsamı dışı.",
        ],
        "pitfalls": [
            "Pazarlama metinlerinde 'tıbbi' iddialar kullanıp intended purpose'u düzgün tanımlamamak.",
            "Ekonomik operatör rollerini (örneğin ithalatçı ve dağıtıcı) karıştırmak.",
        ],
    },
    "Sınıflandırma": {
        "summary": """
Bu modülde cihazların risk sınıflandırması (Class I, IIa, IIb, III) ve Annex VIII sınıflandırma kuralları temel alınarak, kullanım süresi, vücuda invazivlik ve aktif/aktif olmayan cihaz ayrımı incelenir.
""",
        "sections": [
            {
                "title": "1. Sınıflandırmanın Amacı",
                "body": """
Sınıflandırma, cihazın hangi uygunluk değerlendirme yoluna (conformity assessment route) tabi olacağını belirler. Genel kural: **risk ne kadar yüksekse, denetim o kadar sıkıdır**.
"""
            },
            {
                "title": "2. Temel Parametreler",
                "body": """
Annex VIII'e göre sınıflandırma üç ana parametre çevresinde şekillenir:
- Kullanım süresi (geçici, kısa süreli, uzun süreli),
- Vücuda invazivlik durumu (invaziv / non-invaziv / surgically invasive / implantable),
- Aktif/aktif olmayan cihaz ayrımı ve vücutla etkileşimi.

Örneğin:
- Basit bir bandaj → genellikle Class I,
- Kalp pili → Class III,
- Bir infüzyon pompası → genellikle Class IIb.
"""
            },
            {
                "title": "3. Sınıflandırma Kuralları (Annex VIII)",
                "body": """
Annex VIII, kuralları 22 başlık altında toplar. Örneğin:
- Kural 1-4: Non-invaziv cihazlar,
- Kural 5-8: İnvaziv cihazlar,
- Kural 9-13: Aktif cihazlar,
- Kural 14-22: Özel amaçlı cihazlar (ör. kontraseptif cihazlar, dezenfektanlar, vb.).
"""
            },
            {
                "title": "4. Borderline Vakalar",
                "body": """
Bazı ürünler tıbbi cihaz mı, yoksa ilaç mı (veya kozmetik mi) sorusu sınırda kalabilir. Bu durumlarda:
- Etki mekanizması (farmakolojik vs. mekanik),
- Temel amaç,
- Ürünün sunumu (presentation to the user) kritiktir.
"""
            },
        ],
        "key_points": [
            "Sınıflandırma, cihazın tüm regülasyon yolunu belirler.",
            "Annex VIII kuralları birlikte okunmalı, yalnızca tek bir kurala takılı kalınmamalıdır.",
            "Borderline ürünlerde yetkili otorite veya rehber dokümanlara başvurmak gerekir.",
        ],
        "refs": [
            "MDR 2017/745 Annex VIII (Sınıflandırma Kuralları)"
        ],
        "examples": [
            "Akıllı telefonla entegre çalışan EKG patch → genellikle IIa veya IIb.",
            "Dekoratif kontakt lensler → risk durumuna göre IIa/IIb olabilir.",
        ],
        "pitfalls": [
            "Sadece benzer ürünün sınıfına bakıp kendi cihazını analiz etmemek.",
            "Kullanım süresini (duration) yanlış veya eksik tanımlamak.",
        ],
    },
    "Teknik Dosya": {
        "summary": """
Teknik dosya (Technical Documentation), bir cihazın MDR gerekliliklerini karşıladığını kanıtlayan ana dosyadır. Annex II ve III, yapıyı ve PMS ile bağlantısını tanımlar.
""",
        "sections": [
            {
                "title": "1. Teknik Dosyanın Rolü",
                "body": """
Teknik dosya, cihazın güvenlik ve performansına ilişkin tüm kanıtları, tasarım ve üretim bilgilerini, risk yönetimi ve klinik değerlendirme çıktıları ile birlikte sunar.
"""
            },
            {
                "title": "2. Yapısı (Annex II)",
                "body": """
Genel olarak şu başlıklardan oluşur:
- Cihazın genel açıklaması,
- Tasarım ve üretim bilgileri,
- GSPR uyum gösterimi,
- Risk yönetimi dosyası (ISO 14971 ile uyumlu),
- Klinik değerlendirme ve klinik kanıtlar,
- Etiketleme ve kullanma talimatları.
"""
            },
            {
                "title": "3. Annex III – PMS ile İlişki",
                "body": """
Annex III, post-market surveillance (PMS) plan ve raporlarının teknik dosya ile bağlantısını kurar. PMS Plan, PMCF planı ve raporları da teknik dokümantasyonun bir parçası olarak değerlendirilir.
"""
            },
        ],
        "key_points": [
            "Teknik dosya, 'sadece bir klasör' değil; canlı bir yapıdır ve sürekli güncellenmelidir.",
            "Risk yönetimi, klinik değerlendirme ve GSPR uyumu teknik dosyada bütünleşik olmalıdır.",
        ],
        "refs": [
            "MDR 2017/745 Annex II (Technical Documentation)",
            "MDR 2017/745 Annex III (Technical Documentation on PMS)"
        ],
        "examples": [
            "Design dossier mantığından STED yapısına dönüşen bir dosya formatı.",
        ],
        "pitfalls": [
            "Sadece test raporlarını ekleyip GSPR'ye izlenebilirlik (traceability) kurmamak.",
            "PMS çıktılarını teknik dosyaya geri beslememek.",
        ],
    },
    "Klinik Değerlendirme": {
        "summary": """
Klinik değerlendirme, cihazın güvenlik ve performansının klinik açıdan kabul edilebilir olduğuna dair sistematik ve planlı bir süreçtir. Annex XIV bunun çerçevesini verir.
""",
        "sections": [
            {
                "title": "1. Klinik Değerlendirme Planı",
                "body": """
Plan, literatür taraması, eşdeğer cihaz analizi, klinik veri toplama stratejisi ve gerekirse klinik araştırma tasarımını içerir.
"""
            },
            {
                "title": "2. Klinik Veri Kaynakları",
                "body": """
- Yayınlanmış literatür,
- Klinik çalışmalardan elde edilen veriler,
- PMS/PMCF çıktıları,
- Eşdeğer cihaz verileri (sıkı koşullar altında).
"""
            },
            {
                "title": "3. Annex XIV Gereklilikleri",
                "body": """
Annex XIV, klinik değerlendirme raporunun yapısı, güncelleme sıklığı ve PMCF ile olan bağlantıları tanımlar. Yüksek riskli cihazlarda klinik veriye dayalı güçlü ve güncel kanıt beklenir.
"""
            },
        ],
        "key_points": [
            "Klinik değerlendirme tek seferlik bir rapor değil, yaşam döngüsü boyunca güncellenen bir süreçtir.",
            "PMCF ve PMS çıktıları, klinik değerlendirmenin önemli girdileridir.",
        ],
        "refs": [
            "MDR 2017/745 Annex XIV (Klinik Değerlendirme ve Klinikal Araştırmalar)"
        ],
        "examples": [
            "Yeni jenerasyon bir implant için randomize kontrollü çalışma gerekliliği.",
        ],
        "pitfalls": [
            "Eski literatüre dayanarak klinik değerlendirmeyi güncellemeden bırakmak.",
            "Eşdeğer cihaz kavramını yanlış veya yüzeysel kullanmak.",
        ],
    },
    "Risk Yönetimi": {
        "summary": """
Risk yönetimi, ISO 14971'e dayanan, tehlikelerin sistematik olarak tanımlandığı, değerlendirildiği ve risk kontrol önlemleriyle azaltıldığı dinamik bir süreçtir.
""",
        "sections": [
            {
                "title": "1. ISO 14971 Çevrimi",
                "body": """
- Tehlikelerin tanımlanması (Hazard Identification),
- Risk değerlendirmesi (Probability x Severity),
- Risk kontrol önlemlerinin belirlenmesi,
- Kalan riskin değerlendirilmesi ve risk/yarar analizi,
- Üretim sonrası bilgi (post-production information).
"""
            },
            {
                "title": "2. Hazard – Sequence – Situation – Harm",
                "body": """
Modern risk yönetimi, sadece basit 'P x S' tablosu değil, olayların sıralamasını da dikkate alır:
- Hazard: Potansiyel zarar kaynağı (ör. elektrik çarpması),
- Sequence of events: İzolasyon arızası → kaçak akım artışı,
- Hazardous situation: Kullanıcının iletken yüzeye temas etmesi,
- Harm: Yanık, aritmi, ölüm vb.
"""
            },
            {
                "title": "3. Risk Kontrol Hiyerarşisi",
                "body": """
Risk kontrol önlemleri öncelik sırasına göre:
1. Tasarım yoluyla riskin azaltılması,
2. Koruyucu önlemler (guarding, alarm vb.),
3. Kullanıcıya yönelik bilgi (IFU, etiketleme).

Sadece uyarı ve talimatlara dayalı risk kontrolü, genellikle zayıf kabul edilir.
"""
            },
        ],
        "key_points": [
            "Risk yönetimi yaşayan bir süreçtir ve PMS/PMCF ile sürekli beslenmelidir.",
            "Tehlikeleri sadece listelemek yeterli değildir; senaryolaştırmak gerekir.",
        ],
        "refs": [
            "ISO 14971:2019",
            "MDR 2017/745 Annex I (GSPR – Risk Yönetimi ile bağlantılı hükümler)"
        ],
        "examples": [
            "İnfusion pompasında 'over-infusion' riski ve buna karşı alarm sistemi.",
        ],
        "pitfalls": [
            "Tüm riskleri 'medium' işaretlemek, gerçekçi olmayan matrisler oluşturmak.",
            "Post-market verileri risk yönetimine geri beslememek.",
        ],
    },
}

MODULE_QUIZZES = {
    "Giriş & Tanımlar": [
        {
            "question": "Aşağıdakilerden hangisi tıbbi cihaz tanımının merkezinde yer alan temel unsurdur?",
            "options": [
                "Farmakolojik etki ile tedavi etmesi",
                "İnsan üzerinde kullanılmaması",
                "Amaçlanan kullanımın tıbbi bir amaç taşıması",
                "Sadece yazılım olması"
            ],
            "answer": "Amaçlanan kullanımın tıbbi bir amaç taşıması",
            "explanation": "MDR'ye göre tıbbi cihaz tanımında en kritik unsur intended purpose'dır."
        },
        {
            "question": "Aşağıdakilerden hangisi MDR'de ekonomik operatör olarak tanımlanmaz?",
            "options": [
                "Üretici (Manufacturer)",
                "Yetkili Temsilci (Authorised Representative)",
                "İthalatçı (Importer)",
                "Hastane Yönetimi"
            ],
            "answer": "Hastane Yönetimi",
            "explanation": "Hastaneler MDR'de ekonomik operatör olarak sayılmaz; kullanıcı kuruluştur."
        },
        {
            "question": "Aksesuar ile ilgili hangi ifade doğrudur?",
            "options": [
                "Aksesuarlar MDR kapsamına girmez.",
                "Aksesuarlar ilaç gibi değerlendirilir.",
                "Aksesuarlar kendi başına tıbbi amaç taşımaz ama cihazın amacına uygun kullanımını sağlar.",
                "Aksesuarlar yalnızca yazılım olabilir."
            ],
            "answer": "Aksesuarlar kendi başına tıbbi amaç taşımaz ama cihazın amacına uygun kullanımını sağlar.",
            "explanation": "Aksesuar, tıbbi cihazın kullanımını mümkün kılan veya destekleyen üründür ve MDR kapsamındadır."
        },
    ],
    "Sınıflandırma": [
        {
            "question": "Sınıflandırma için temel referans doküman hangisidir?",
            "options": [
                "Annex II",
                "Annex III",
                "Annex VIII",
                "Annex XIV"
            ],
            "answer": "Annex VIII",
            "explanation": "Annex VIII, MDR kapsamında sınıflandırma kurallarını tanımlar."
        },
        {
            "question": "Genellikle en yüksek risk seviyesine sahip sınıf hangisidir?",
            "options": ["Class I", "Class IIa", "Class IIb", "Class III"],
            "answer": "Class III",
            "explanation": "Class III cihazlar en yüksek riskli cihazlardır (örneğin kalp pili, stent vb.)."
        },
        {
            "question": "Aşağıdakilerden hangisi sınıflandırmada dikkate alınan parametrelerden BİRİ DEĞİLDİR?",
            "options": [
                "Kullanım süresi",
                "Vücuda invazivlik durumu",
                "Cihazın rengi",
                "Aktif/aktif olmayan cihaz ayrımı"
            ],
            "answer": "Cihazın rengi",
            "explanation": "Renk sınıflandırma için bir kriter değildir; kullanım süresi, invazivlik ve aktiflik önemlidir."
        },
    ],
    "Teknik Dosya": [
        {
            "question": "Teknik dosyanın ana amacı nedir?",
            "options": [
                "Sadece pazarlama materyallerini saklamak",
                "Cihazın MDR gerekliliklerini karşıladığını kanıtlamak",
                "Sadece test raporlarını arşivlemek",
                "Sadece üretim talimatlarını içermek"
            ],
            "answer": "Cihazın MDR gerekliliklerini karşıladığını kanıtlamak",
            "explanation": "Teknik dosya, cihazın güvenli ve performanslı olduğunu gösteren tüm kanıtları içerir."
        },
        {
            "question": "Teknik dosyanın yapısını tarif eden ek hangisidir?",
            "options": ["Annex I", "Annex II", "Annex VIII", "Annex XIV"],
            "answer": "Annex II",
            "explanation": "Annex II, teknik dokümantasyonun içerik başlıklarını tanımlar."
        },
        {
            "question": "PMS ile teknik dosya bağlantısını hangi ek tanımlar?",
            "options": ["Annex III", "Annex V", "Annex VII", "Annex IX"],
            "answer": "Annex III",
            "explanation": "Annex III, PMS ile ilişkili teknik dokümantasyon gerekliliklerini açıklar."
        },
    ],
    "Klinik Değerlendirme": [
        {
            "question": "Klinik değerlendirmenin temel amacı nedir?",
            "options": [
                "Sadece pazarda rekabet analizi yapmak",
                "Cihazın klinik güvenlik ve performansını göstermek",
                "Sadece literatür taraması yapmak",
                "Cihazın maliyetini hesaplamak"
            ],
            "answer": "Cihazın klinik güvenlik ve performansını göstermek",
            "explanation": "Klinik değerlendirme, cihazın beklenen klinik fayda ve risk profilini kanıtlar."
        },
        {
            "question": "Klinik veri kaynağı olarak AŞAĞIDAKİLERDEN hangisi kullanılamaz?",
            "options": [
                "Yayınlanmış literatür",
                "Klinik çalışmalar",
                "PMS/PMCF çıktıları",
                "Rastgele sosyal medya yorumları"
            ],
            "answer": "Rastgele sosyal medya yorumları",
            "explanation": "Klinik veri, sistematik ve doğrulanabilir kaynaklara dayanmalıdır."
        },
        {
            "question": "Klinik değerlendirme ve klinik araştırmaları tanımlayan ek hangisidir?",
            "options": ["Annex I", "Annex II", "Annex VIII", "Annex XIV"],
            "answer": "Annex XIV",
            "explanation": "Annex XIV, klinik değerlendirme ve klinik araştırmalara ilişkin gereklilikleri içerir."
        },
    ],
    "Risk Yönetimi": [
        {
            "question": "Risk yönetimi için temel referans standart hangisidir?",
            "options": [
                "ISO 13485",
                "ISO 14971",
                "ISO 9001",
                "EN 62366"
            ],
            "answer": "ISO 14971",
            "explanation": "ISO 14971 tıbbi cihazlar için risk yönetimi standardıdır."
        },
        {
            "question": "Aşağıdakilerden hangisi risk kontrol hiyerarşisinde en üstte yer alır?",
            "options": [
                "Kullanıcıya uyarı eklemek",
                "Tasarımla riskin azaltılması",
                "Kullanma talimatı yazmak",
                "Etiketlemeye dikkat çekici semboller eklemek"
            ],
            "answer": "Tasarımla riskin azaltılması",
            "explanation": "Risk kontrolünde öncelik, tasarım yoluyla risk azaltmadır."
        },
        {
            "question": "Hazard → Sequence → Hazardous situation → Harm zinciri neyi temsil eder?",
            "options": [
                "Kalite yönetim süreçlerini",
                "Klinik araştırma fazlarını",
                "Risk senaryosu modellemesini",
                "PMS raporlama basamaklarını"
            ],
            "answer": "Risk senaryosu modellemesini",
            "explanation": "Bu zincir, tehlikenin zarar ile sonuçlanmasına giden olaylar zincirinin modellenmesidir."
        },
    ],
}

# V5.0 – Denetim Senaryoları
AUDIT_SCENARIOS = {
    "Class I – Basit Non-invaziv Cihaz Denetimi": """
Class I, non-steril, ölçüm fonksiyonu olmayan, non-invaziv bir cihazın MDR kapsamında genel denetimi.
Odak: temel GSPR uyumu, teknik dosya içeriği, etiketleme, UDI ve PMS yapısı.
""",
    "Implantable Class IIb – Ortopedik Cihaz Denetimi": """
Implantable Class IIb (örneğin ortopedik plak/vida) bir cihaz için denetim.
Odak: risk yönetimi, klinik değerlendirme derinliği, PMCF gerekliliği, sterilite ve üretim proses validasyonu.
""",
    "Software as Medical Device (SaMD) Denetimi": """
Yalnızca yazılım olarak tıbbi cihaz (SaMD) denetimi.
Odak: intended purpose, risk sınıflandırması, yazılım yaşam döngüsü, siber güvenlik, klinik değerlendirme ve post-market gözetim.
""",
    "Class III – EC Sertifika Yenileme Denetimi": """
Class III implantable bir cihaz için EC sertifika yenileme (surveillance / renewal) denetimi.
Odak: PMS/PMCF çıktılarının teknik dosyaya geri beslenmesi, ciddi olay raporlamaları, kalan riskin kabul edilebilirliği ve klinik kanıtların güncelliği.
"""
}

# -----------------------------------------------------------------------------
# 3. YARDIMCI FONKSİYONLAR
# -----------------------------------------------------------------------------
def get_active_api_key_value():
    """Önce session_state.api_key, yoksa st.secrets içindeki GOOGLE_API_KEY."""
    if "api_key" in st.session_state and st.session_state.api_key:
        return st.session_state.api_key
    try:
        if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    return None


def get_working_model(api_key: str):
    """Mevcut ve çalışan bir Gemini modelini seçer."""
    if not api_key:
        raise ValueError("Google API anahtarı gerekli.")
    api_key = api_key.strip()
    genai.configure(api_key=api_key, transport="rest")

    if "working_model_name" in st.session_state:
        return genai.GenerativeModel(st.session_state.working_model_name)

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
    ]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            st.session_state.working_model_name = model_name
            return model
        except Exception:
            continue

    return genai.GenerativeModel(models_to_try[0])


def handle_api_error(e: Exception):
    msg = str(e)
    lower = msg.lower()
    if "429" in msg and "quota" in lower:
        st.error(
            "⚠️ Google Gemini API kota limitin dolmuş görünüyor.\n\n"
            "- Google AI Studio / ai.google.dev panelinden kullanım ve faturalandırma ayarlarını kontrol etmelisin.\n"
            "- Kota yenilenene veya limit artırılana kadar bu uygulama yeni yanıt üretemeyecek."
        )
    else:
        st.error(f"Beklenmeyen bir hata oluştu:\n\n{msg}")


@st.cache_resource
def load_all_pdfs(folder_path="dokumanlar"):
    full_text = ""
    file_list = []
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return "", []

    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"
            file_list.append(filename)
        except Exception:
            pass
    return full_text, file_list


def detect_context_focus(context_text: str):
    if not context_text:
        return None
    keywords = [
        "gspr", "annex i", "annex ii", "annex iii", "annex viii", "annex xiv",
        "iso 14971", "iso 13485", "pms", "pmcf", "risk", "risk management",
        "sınıflandırma", "classification", "technical documentation",
        "teknik dosya", "clinical evaluation", "klinik değerlendirme"
    ]
    text_lower = context_text.lower()
    best_kw = None
    best_count = 0
    for kw in keywords:
        c = text_lower.count(kw)
        if c > best_count:
            best_count = c
            best_kw = kw
    return best_kw


def generate_ai_question(api_key, context_text, difficulty="Orta", qtype="Çoktan Seçmeli"):
    try:
        model = get_working_model(api_key)

        if len(context_text) > 5000:
            start = random.randint(0, len(context_text) - 4000)
            partial_context = context_text[start: start + 4000]
        else:
            partial_context = context_text

        focus = detect_context_focus(context_text)
        focus_text = f"Özellikle '{focus}' temalı bir soru hazırla." if focus else ""

        diff_map = {
            "Temel": "temel seviye, kavram tanımları ve kolay örnekler içeren",
            "Orta": "orta seviye, kavramlar arası ilişki ve basit yorum içeren",
            "İleri": "ileri seviye, denetçi bakışı ve karmaşık senaryolar içeren"
        }
        diff_desc = diff_map.get(difficulty, "orta seviye")

        if qtype == "Çoktan Seçmeli":
            tur = "coktan_secme"
            type_hint = "4 şıklı bir çoktan seçmeli sınav sorusu hazırla."
        elif qtype == "Doğru/Yanlış":
            tur = "dogru_yanlis"
            type_hint = "Doğru/Yanlış tipinde tek bir cümlelik bir soru hazırla."
        elif qtype == "Vaka Analizi":
            tur = "vaka"
            type_hint = "Kısa bir vaka senaryosu ver ve kullanıcıdan MDR kapsamında değerlendirme yapmasını iste."
        else:
            tur = "acik_uclu"
            type_hint = "Kısa ama derinlikli bir açık uçlu soru hazırla."

        prompt = f"""
Sen MDR 2017/745 ve ilgili ISO standartları konusunda uzman bir sınav hazırlayıcısın.
Aşağıdaki bağlam metni üzerinden {diff_desc} bir sınav sorusu hazırlayacaksın.

BAĞLAM:
{partial_context}

{focus_text}

Soru tipi: {qtype} ({type_hint})

Lütfen SADECE aşağıdaki JSON formatında cevap ver:
{{
  "soru": "Soru metni... (Türkçe)",
  "tur": "{tur}",
  "secenekler": ["A...", "B...", "C...", "D..."],
  "dogru_cevap": "Doğru cevap metni veya ideal cevap",
  "aciklama": "Doğru cevabın açıklaması",
  "ipuclari": "Öğrenmeyi destekleyici kısa ipuçları"
}}

NOTLAR:
- Eğer soru tipi 'Doğru/Yanlış' ise "secenekler" alanını ["Doğru","Yanlış"] şeklinde doldur.
- Eğer soru tipi 'Vaka Analizi' veya 'Açık Uçlu' ise "secenekler" alanını boş liste yap: [].
- "tur" alanı mutlaka şu değerlerden biri olmalıdır: "coktan_secme", "dogru_yanlis", "vaka", "acik_uclu".
"""
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        if "tur" not in data:
            data["tur"] = "coktan_secme"
        return data
    except Exception:
        return None


def grade_open_answer(api_key, question_dict, user_answer, difficulty="Orta"):
    try:
        model = get_working_model(api_key)
        ideal_answer = question_dict.get("dogru_cevap", "")
        soru = question_dict.get("soru", "")

        prompt = f"""
Sen MDR 2017/745 kapsamında deneyimli bir denetçisin.
Aşağıdaki soru ve ideal cevaba göre kullanıcının cevabını değerlendir.
Zorluk seviyesi: {difficulty}

Soru: {soru}

İdeal cevap (referans amaçlı): {ideal_answer}

Kullanıcının cevabı: {user_answer}

Lütfen 0-100 arasında bir puan ver ve SADECE aşağıdaki JSON formatında cevap ver:
{{
  "puan": 0-100 arası bir tamsayı,
  "degerlendirme": "Genel olarak cevabın ne kadar iyi olduğunu anlatan kısa bir paragraf.",
  "eksikler": "Eksik veya yanlış bırakılan önemli noktaların listesi veya açıklaması.",
  "guclu_yonler": "Cevabın güçlü yönleri, iyi yakalanan noktalar."
}}
"""
        res = model.generate_content(prompt).text
        clean = res.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except Exception:
        return None


def build_assistant_prompt(mode: str, ctx: str, user_message: str, focus: str | None):
    base_format = """
Cevap formatın MUTLAKA şu yapıda olmalıdır (Türkçe):

Özet:
- 3–5 maddede en önemli noktaları özetle.

Detaylı Açıklama:
- Konuyu sistematik ve eğitim odaklı şekilde derinlemesine açıkla.
- Gerekirse madde madde ve alt başlıklar kullan.

Kaynaklar:
- İlgili MDR maddelerini ve eklerini maddeler hâlinde yaz (örneğin: "MDR 2017/745 Madde 2", "Annex II", "Annex VIII").
- İlgili ISO standartları varsa belirt (örneğin: "ISO 14971:2019", "ISO 13485:2016").
"""
    focus_text = f"Bağlamda baskın konu: {focus}. Bu alanı cevabında özellikle vurgula.\n" if focus else ""

    if mode == "Eğitmen Modu":
        role_text = """
Rolün: MDR 2017/745 ve ilgili ISO standartları konusunda deneyimli bir EĞİTMEN'sin.
Amacın: Kullanıcının kavramı gerçekten anlamasını sağlamak, örneklerle anlatmak ve yanlış anlaşılmaları gidermek.
"""
    elif mode == "Denetçi Modu":
        role_text = """
Rolün: Notified Body denetçisi gibi davranan katı bir DENETÇİ'sin.
Amacın: Kullanıcının yaklaşımındaki eksikleri, riskleri ve uyumsuzlukları dürüstçe ve doğrudan ortaya koymak; gerektiğinde ek sorular sorarak onu zorlamak.
"""
    elif mode == "Teknik Dosya Modu":
        role_text = """
Rolün: Annex II ve Annex III'e hâkim, tecrübeli bir TEKNİK DOSYA UZMANI'sın.
Amacın: Kullanıcıya teknik dosya (Annex II) ve PMS dokümantasyonu (Annex III) hazırlama, yapılandırma ve içerik kurgusu konusunda net yol göstermek.
Özellikle izlenebilirlik (traceability) ve GSPR kapsamasına vurgu yap.
"""
    elif mode == "Risk Analizi Modu":
        role_text = """
Rolün: ISO 14971 ve MDR risk yönetimi hükümlerine hâkim bir RİSK YÖNETİMİ UZMANI'sın.
Amacın: Hazard → Sequence of Events → Hazardous Situation → Harm zincirini kullanarak kullanıcıya sağlam risk senaryoları kurdurmak, risk kontrol hiyerarşisine uygun önlemler önermek ve kalan risk değerlendirmesi hakkında rehberlik etmek.
"""
    else:
        role_text = """
Rolün: MDR 2017/745 ve ilgili ISO standartlarında uzman bir danışmansın.
Amacın: Kullanıcının sorusuna mümkün olan en net ve regülasyona dayalı cevabı vermek.
"""

    prompt = f"""
{role_text}

{base_format}

{focus_text}

EĞİTİM BAĞLAMI (MDR/ISO dokümanları ve ders notları):
{ctx}

KULLANICININ SORUSU / TALEBİ:
{user_message}
"""
    return prompt


def start_audit_session(api_key: str, scenario_key: str, context_text: str):
    model = get_working_model(api_key)
    scenario_desc = AUDIT_SCENARIOS.get(scenario_key, "")
    ctx = context_text[:1500] if context_text else ""
    prompt = f"""
Sen MDR 2017/745 kapsamında çok deneyimli bir Notified Body denetçisisin.

Denetim senaryosu:
{scenario_desc}

Elinde cihazın teknik dosyası ve kalite sistemi kayıtları var (Annex II, Annex III, ISO 13485 kayıtları vb.).

Şimdi kullanıcı ile sözlü bir denetim yapıyorsun. Bu senaryo için:
- Kullanıcının hem MDR hem de ilgili ISO standartlarını (özellikle ISO 13485 ve ISO 14971) ne kadar bildiğini ölçecek şekilde TEK bir zorlayıcı soru sor.
- Soru, açık uçlu olsun (kullanıcıdan açıklama bekle).
- Tercihen GSPR, risk yönetimi, klinik değerlendirme veya PMS/PMCF ile bağlantı kur.

Sadece soruyu yaz, başka hiçbir açıklama yazma.
"""
    res = model.generate_content(prompt).text
    return res.strip(), scenario_desc


def evaluate_audit_answer(api_key: str, scenario_desc: str, question: str, answer: str):
    model = get_working_model(api_key)
    prompt = f"""
Sen MDR 2017/745 kapsamında sert bir Notified Body denetçisisin.

Denetim senaryosu: {scenario_desc}

Sorduğun soru: {question}
Kullanıcının cevabı: {answer}

Bu cevabı değerlendir:
- 0 ile 5 arasında bir puan ver (5: mükemmel, 0: tamamen yanlış).
- Cevabın güçlü ve zayıf yönlerini açıklayan kısa ama net bir değerlendirme yap.
- MDR veya ISO 13485/14971 açısından eksik, yanlış veya riskli gördüğün her noktayı non-conformity (NC) şeklinde listele.
  Örnek: "NC1: Annex II teknik dokümantasyonda GSPR izlenebilirliği gösterilmemiş."
- Aynı senaryo için bir sonraki zorlayıcı soruyu üret.
- Eğer bu oturum için artık ek soru sormaya gerek yoksa 'tamamlandi_mi' alanını true yap ve 'sonraki_soru' alanını boş string bırak.

Sadece aşağıdaki JSON formatında cevap ver:
{{
  "puan": 0,
  "degerlendirme": "Kısa değerlendirme metni",
  "nc_listesi": ["NC1: ...", "NC2: ..."],
  "sonraki_soru": "Bir sonraki soru metni veya boş string",
  "tamamlandi_mi": false
}}
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean)
    except Exception:
        data = {
            "puan": 0,
            "degerlendirme": "Değerlendirme sırasında JSON parse hatası oluştu. Lütfen tekrar deneyin.",
            "nc_listesi": [],
            "sonraki_soru": "",
            "tamamlandi_mi": True
        }
    data.setdefault("puan", 0)
    data.setdefault("degerlendirme", "")
    data.setdefault("nc_listesi", [])
    data.setdefault("sonraki_soru", "")
    data.setdefault("tamamlandi_mi", False)
    return data


# --- V6.0: Otomatik GSPR Matrisi üretimi ---
def generate_gspr_matrix(api_key: str, device_name: str, device_desc: str, context_text: str):
    model = get_working_model(api_key)
    ctx = context_text[:4000] if context_text else ""
    prompt = f"""
Sen MDR 2017/745 Annex I (GSPR) konusunda uzman bir regülasyon danışmanısın.

Cihaz adı: {device_name}
Cihaz tanımı / intended purpose özeti: {device_desc}

Bağlam (MDR/ISO dokümanları, ders notları vb.):
{ctx}

Bu bilgiler ışığında, cihaz için uygulanabilir GSPR maddeleri için özet bir GSPR matrisi hazırla.
Lütfen SADECE şu formatta JSON ver:
[
  {{
    "gspr_no": "1",
    "baslik": "Genel güvenlik ve performans gereklilikleri",
    "gereklilik_ozeti": "Kısa açıklama...",
    "uygulanabilirlik": "Uygulanır" veya "Uygulanmaz (gerekçeli)",
    "uygunluk_gosterimi": "Hangi standartlar, testler, dokümanlarla bu gereklilik karşılanıyor (kısaca)",
    "dokuman_referansi": "İlgili teknik dosya bölüm(ler)i (ör. GSPR matrisi, test raporları, risk yönetimi dosyası vb.)"
  }}
]

- Liste içerisinde en az 8–10 GSPR maddesi olsun.
- gspr_no alanında Annex I referans numarasını (örneğin '1', '2', '3', '9.1', '9.2' gibi) belirt.
- Özellikle risk yönetimi, klinik değerlendirme, kimyasal/biyolojik güvenlik ve kullanılabilirlikle ilgili GSPR'leri eklemeye çalış.
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data


# --- V6.0: Otomatik Risk Analizi Tablosu üretimi ---
def generate_risk_table(api_key: str, device_name: str, device_desc: str, context_text: str):
    model = get_working_model(api_key)
    ctx = context_text[:4000] if context_text else ""
    prompt = f"""
Sen ISO 14971:2019 ve MDR Annex I risk yönetimi hükümlerine çok hâkim bir risk uzmanısın.

Cihaz adı: {device_name}
Cihaz tanımı / intended purpose özeti: {device_desc}

Bağlam (MDR/ISO dokümanları, ders notları vb.):
{ctx}

Bu bilgiler ışığında, cihaz için örnek bir risk analizi tablosu hazırla.
Lütfen SADECE şu formatta JSON ver:
[
  {{
    "hazard": "Örneğin: Elektrik çarpması",
    "sequence_of_events": "İzolasyon arızası → kaçak akım artışı → kullanıcı metal yüzeye temas eder",
    "hazardous_situation": "Kullanıcının kaçak akım taşıyan yüzeye teması",
    "harm": "Yanık, aritmi, ölüm",
    "initial_severity": "S1-S5 arasında bir seviye (kendi tanımına göre)",
    "initial_probability": "P1-P5 arasında bir seviye",
    "risk_controls": "Tasarım, koruyucu önlemler, bilgi/etiketleme şeklinde özetle",
    "residual_severity": "Kontroller sonrasındaki şiddet seviyesi (S1-S5)",
    "residual_probability": "Kontroller sonrasındaki olasılık seviyesi (P1-P5)",
    "risk_evaluation": "Kalan risk kabul edilebilir mi? Kabul kriterine atıf yap."
  }}
]

- Liste içerisinde en az 6–8 farklı risk senaryosu olsun.
- Hem elektriksel, hem mekanik, hem de yazılım/hata/uygulama kaynaklı risklerden örnekler ver.
- En az bir tanesi kullanılabilirlik hatasından kaynaklanan risk olsun.
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data


# --- V7.0: GSPR ↔ Risk İzlenebilirlik Matrisi ---
def generate_traceability_matrix(api_key: str, gspr_rows, risk_rows):
    model = get_working_model(api_key)
    prompt = f"""
Sen MDR Annex I (GSPR) ve ISO 14971 risk yönetimi konusunda uzman bir sistem mühendisisin.

Elinde aşağıdaki iki liste var:

GSPR_LIST:
{json.dumps(gspr_rows, ensure_ascii=False)}

RISK_LIST:
{json.dumps(risk_rows, ensure_ascii=False)}

Görev:
- Her RISK_LIST elemanı için 1–4 adet en ilgili GSPR maddesini eşleştir.
- Eşleştirme yaparken hazard, hazardous situation ve harm açıklamalarına bak.
- Özellikle risk yönetimi, klinik performans, kimyasal/biyolojik güvenlik ve kullanılabilirlik ile ilgili GSPR'lere öncelik ver.

Lütfen SADECE şu JSON formatında cevap ver:
[
  {{
    "risk_index": 0,
    "risk_ozet": "Kısa bir risk özeti (hazard / harm merkezli)",
    "gspr_list": ["1", "9.2", "14.1"]
  }}
]

Notlar:
- risk_index, RISK_LIST içindeki index (0'dan başlayarak).
- gspr_list, GSPR_LIST içindeki 'gspr_no' alanlarıdır.
- Tüm riskler için (RISK_LIST'teki her eleman) bir kayıt oluştur.
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data


# --- V8.0: Denetim Checklisti & Test Planı Üretimi ---
def generate_checklist_and_testplan(api_key: str, device_name: str, gspr_rows, risk_rows, trace_matrix):
    """İzlenebilirlik verisini kullanarak denetim checklisti ve test planı üretir."""
    model = get_working_model(api_key)
    prompt = f"""
Sen MDR 2017/745, Annex I (GSPR), Annex II/III (Teknik Doküman) ve ISO 14971/13485 konularında çok tecrübeli bir Notified Body denetçisi ve test planlayıcısın.

Cihaz adı: {device_name}

Elindeki bilgiler:
GSPR_LIST:
{json.dumps(gspr_rows, ensure_ascii=False)}

RISK_LIST:
{json.dumps(risk_rows, ensure_ascii=False)}

TRACE_MATRIX (Risk -> GSPR eşleşmeleri):
{json.dumps(trace_matrix, ensure_ascii=False)}

Görev:

1) Bu verilere dayanarak, denetim sırasında kullanılabilecek bir "Denetim Checklisti" üret.
   - Her madde belirli bir GSPR ve/veya risk senaryosuna referans versin.
   - Her madde için neyin kontrol edileceğini ve kanıt olarak hangi kayıt/dokümanların talep edilmesi gerektiğini yaz.
   - Tip alanında "Dokümantasyon", "Kayıt", "Saha Gözlemi", "Test" gibi değerler kullan.

2) Aynı veriye dayanarak, cihaz için özet bir "Test Planı" üret.
   - Her test için test_adi, amaç, ilişkili GSPR numaraları, ilişkili risk indexleri, test_tipi (Fonksiyonel, Güvenlik, Kullanılabilirlik, Klinik vb.) ve öncelik (Yüksek/Orta/Düşük) belirt.

Lütfen SADECE aşağıdaki JSON formatında cevap ver:
{{
  "denetim_checklist": [
    {{
      "madde": "Kontrol edilecek madde açıklaması",
      "kaynak": "Örneğin: GSPR 9.2, Risk #3",
      "tip": "Dokümantasyon"
    }}
  ],
  "test_plan": [
    {{
      "test_adi": "Örneğin: Elektriksel güvenlik testi",
      "amac": "Bu test ile doğrulanacak güvenlik/performans amacı",
      "iliskili_gspr": ["1", "9.2"],
      "iliskili_riskler": [0, 3],
      "test_tipi": "Güvenlik",
      "oncelik": "Yüksek"
    }}
  ]
}}

Notlar:
- denetim_checklist listesinde en az 10-15 madde olsun.
- test_plan listesinde en az 6-8 test tanımı olsun.
- Metinlerin tamamı Türkçe olsun.
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data


# --- Yeni: Stok ürünü için sınıflandırma + istasyon talimatları ---
def classify_and_build_work_instructions(api_key: str, device_name: str, device_desc: str, context_text: str):
    """
    Bir ürün için:
    - MDR sınıfı tahmini (Class I / IIa / IIb / III + gerekçe)
    - Her istasyon için kullanım kılavuzu (operatör talimatı) üretir.
    """
    model = get_working_model(api_key)
    ctx = context_text[:4000] if context_text else ""
    prompt = f"""
Sen MDR 2017/745 sınıflandırma (Annex VIII) ve tıbbi cihaz üretim prosesleri konusunda uzman bir danışmansın.

Cihaz/Ürün adı: {device_name}
Ürün tanımı / intended purpose: {device_desc}

Üretim istasyonları:
1. Sayım
2. Kumlama
3. Polisaj
4. Lazer Markalama
5. Altın Kaplama
6. Yıkama
7. Paketleme
8. Kalite Kontrol

Bağlam (MDR/ISO metinleri, teknik dokümanlar, ders notları):
{ctx}

Görevlerin:

1) Bu ürünün MDR kapsamındaki OLASI risk sınıfını (Class I, Class IIa, Class IIb veya Class III) tahmini olarak değerlendir ve kısa gerekçe yaz.
   (Steril / non-steril, ölçüm fonksiyonlu, reusable vb. özellikleri de yorumlayabilirsin.)

2) Yukarıdaki HER bir istasyon için, üretim operatörüne yönelik kısa ama profesyonel bir "istasyon kullanım kılavuzu" hazırla:
   - İstasyonun amacı,
   - 5–10 maddelik kritik adımlar / dikkat edilmesi gereken noktalar,
   - Tutulması gereken kayıt/doküman türleri (örn. lot no, proses parametreleri, operatör imzası).

3) MDR ve ilgili ISO (özellikle ISO 13485 ve ISO 14971) gerekliliklerine uygun bir dil kullan.

SADECE aşağıdaki JSON formatında cevap ver:
{{
  "urun_adi": "{device_name}",
  "onerilen_sinif": "Class ...",
  "sinif_gerekcesi": "Bu sınıfın seçilme gerekçesi...",
  "istasyon_talimatlari": {{
    "sayim": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "kumlama": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "polisaj": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "lazer_markalama": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "altin_kaplama": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "yikama": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "paketleme": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }},
    "kalite_kontrol": {{
      "amaç": "...",
      "kritik_noktalar": ["...", "..."],
      "kayıtlar": ["...", "..."]
    }}
  }}
}}

NOTLAR:
- İstasyon anahtarları MUTLAKA şu isimler olsun: "sayim", "kumlama", "polisaj", "lazer_markalama", "altin_kaplama", "yikama", "paketleme", "kalite_kontrol".
- Tüm metinler Türkçe olsun.
- Sınıf tahmini eğitim amaçlıdır; gerçek regülatuvar karara eşdeğer olmadığı belirtilmiş kabul edilebilir.
"""
    res = model.generate_content(prompt).text
    clean = res.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return data


# --- Yardımcı fonksiyonlar: MC cevap eşleştirme ---
def _normalize_text(s: str) -> str:
    """Boşluk ve büyük/küçük harf duyarsız karşılaştırma için normalize eder."""
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().split())


def get_canonical_correct_option(question_dict):
    """
    Gemini'nin ürettiği JSON içinden gerçek doğru şıkkı bulur.
    """
    options = question_dict.get("secenekler") or []
    correct_raw = (question_dict.get("dogru_cevap") or "").strip()

    if not options:
        return correct_raw

    # 1) dogru_cevap doğrudan şıklardan biri mi?
    for opt in options:
        if _normalize_text(opt) == _normalize_text(correct_raw):
            return opt

    # 2) dogru_cevap sadece harf mi? (A, B, C, D...)
    labels = ["A", "B", "C", "D", "E", "F"]
    cr_up = correct_raw.upper()
    if cr_up in labels:
        idx = labels.index(cr_up)
        if idx < len(options):
            return options[idx]

    # 3) dogru_cevap ile şıklar arasında alt/üst string eşleşmesi var mı?
    norm_raw = _normalize_text(correct_raw)
    for opt in options:
        nopt = _normalize_text(opt)
        if nopt and (nopt in norm_raw or norm_raw in nopt):
            return opt

    # 4) Hiçbiri olmadıysa, eldeki raw metni döndür (fallback)
    return correct_raw


# -----------------------------------------------------------------------------
# 4. SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎓 Denizin Akademi v8.1")

    # API kayıt alanı
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    st.markdown("### 🔐 API Ayarları")

    # Secrets var mı?
    has_secret = False
    try:
        if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
            has_secret = True
    except Exception:
        has_secret = False

    # API kaynağı seçimi
    default_index = 0 if st.session_state.api_key or has_secret else 1
    api_mode = st.radio(
        "API Anahtarı Kaynağı",
        ["Kayıtlı Anahtarı Kullan", "Yeni Anahtar Gir"],
        index=default_index
    )

    if api_mode == "Kayıtlı Anahtarı Kullan":
        active_key = get_active_api_key_value()
        if active_key:
            st.success("Kayıtlı bir API anahtarı mevcut. Uygulama bu anahtarı kullanacak.")
        else:
            st.warning("Kayıtlı bir API anahtarı yok. Aşağıdan yeni bir anahtar girmen gerekiyor.")
    else:
        new_key = st.text_input("🔑 Google API Anahtarı", type="password")
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            if st.button("Anahtarı Kaydet", key="save_api"):
                if new_key:
                    st.session_state.api_key = new_key.strip()
                    st.success("API anahtarı bu oturum için kaydedildi.")
                else:
                    st.error("Boş anahtar kaydedilemez.")
        with col_k2:
            if st.button("Kayıtlı Anahtarı Temizle", key="clear_api"):
                st.session_state.api_key = ""
                st.info("Kayıtlı API anahtarı temizlendi.")

    st.markdown("---")
    st.markdown("#### 📂 Doküman Yönetimi")
    context_text, loaded_files = load_all_pdfs()
    if loaded_files:
        st.success(f"{len(loaded_files)} Belge Aktif")
    else:
        st.warning("Belge Yok! 'dokumanlar' klasörünü kontrol et.")

    if 'working_model_name' in st.session_state:
        st.caption(f"🚀 Aktif Model: {st.session_state.working_model_name}")

    if "gspr_matrix" in st.session_state and "risk_table" in st.session_state:
        st.markdown("#### 🔗 İzlenebilirlik Durumu")
        st.caption(f"GSPR satır sayısı: {len(st.session_state.get('gspr_matrix', []))}")
        st.caption(f"Risk senaryosu sayısı: {len(st.session_state.get('risk_table', []))}")

# Sidebar sonrası aktif API anahtarını çek
api_key = get_active_api_key_value()

# -----------------------------------------------------------------------------
# 5. ANA EKRAN
# -----------------------------------------------------------------------------
st.markdown(
    '<div class="header-box"><h1>🏥 MDR Uzmanlık Akademisi v8.1</h1></div>',
    unsafe_allow_html=True
)

tab_egitim, tab_quiz, tab_asistan, tab_auditor, tab_docgen, tab_trace, tab_plan, tab_stock = st.tabs([
    "📚 Eğitim",
    "🧠 Soru Bankası",
    "🤖 MDR Asistanı",
    "🎭 Sanal Denetçi",
    "📝 Doküman Fabrikası",
    "🔗 İzlenebilirlik",
    "📋 Checklist & Test Plan",
    "🏭 Stok & Proses Analizi"
])

# --- TAB 1: EĞİTİM ---
with tab_egitim:
    col1, col2 = st.columns([1, 3])
    with col1:
        modul = st.radio(
            "Modül:",
            ["Giriş & Tanımlar", "Sınıflandırma", "Teknik Dosya", "Klinik Değerlendirme", "Risk Yönetimi"]
        )
    with col2:
        lesson = LESSONS[modul]
        st.info(f"Seçilen Modül: {modul}")

        st.markdown("### 📌 Modül Özeti")
        st.markdown(lesson["summary"])

        st.markdown("### 🧩 Kavramsal Harita (Infografik Tarzı)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""
                <div class="info-card">
                    <b>👀 Odak Noktası</b><br>
                    {modul} modülünün temel amacı, MDR kapsamında bu başlığın neyi temsil ettiğini ve diğer modüllerle ilişkisini kavratmaktır.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="info-card">
                    <b>🔗 İlişkili Modüller</b><br>
                    - Teknik Dosya ile izlenebilirlik<br>
                    - Risk Yönetimi ile güvenlik<br>
                    - Klinik Değerlendirme ile klinik kanıt<br>
                    - PMS/PMCF ile yaşam döngüsü yaklaşımı
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 📚 Detaylı Ders Notları")
        for section in lesson["sections"]:
            with st.expander(section["title"], expanded=False):
                st.markdown(section["body"])

        st.markdown("### ⚠️ Kritik Noktalar")
        for kp in lesson["key_points"]:
            st.markdown(f"- {kp}")

        st.markdown("### 📖 İlgili MDR / ISO Referansları")
        for r in lesson["refs"]:
            st.markdown(f"- {r}")

        if lesson["examples"]:
            st.markdown("### 🧪 Örnek Cihaz / Senaryolar")
            for ex in lesson["examples"]:
                st.markdown(f"- {ex}")

        if lesson["pitfalls"]:
            st.markdown("### ❗ Sık Yapılan Hatalar")
            for pit in lesson["pitfalls"]:
                st.markdown(f"- {pit}")

        st.markdown("---")
        st.markdown("### 🧠 Mini Quiz — Bu modülü ne kadar anladın?")
        questions = MODULE_QUIZZES[modul]
        for idx, q in enumerate(questions):
            st.markdown(f"**Soru {idx+1}: {q['question']}**")
            st.radio(
                "Seçimin:",
                q["options"],
                key=f"edu_{modul}_q{idx}",
                label_visibility="collapsed"
            )

        if st.button("✅ Cevapları Kontrol Et", key="edu_quiz_check"):
            correct = 0
            total = len(questions)
            st.markdown("#### Sonuçlar:")
            for idx, q in enumerate(questions):
                user_answer = st.session_state.get(f"edu_{modul}_q{idx}")
                if user_answer == q["answer"]:
                    correct += 1
                    st.success(f"Soru {idx+1}: Doğru ✅\n\nAçıklama: {q['explanation']}")
                else:
                    st.error(
                        f"Soru {idx+1}: Yanlış ❌\n"
                        f"Senin cevabın: **{user_answer}**\n\n"
                        f"Doğru cevap: **{q['answer']}**\n\n"
                        f"Açıklama: {q['explanation']}"
                    )
            st.info(f"Toplam Skor: {correct} / {total}")

# --- TAB 2: QUIZ (Gelişmiş Soru Bankası + Fixli) ---
with tab_quiz:
    st.markdown("### 🧠 Gelişmiş Soru Bankası (V3.1 – Widget Key Fix)")

    # State init
    if "current_q" not in st.session_state:
        st.session_state.current_q = None
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "current_q_difficulty" not in st.session_state:
        st.session_state.current_q_difficulty = "Orta"
    if "current_q_type" not in st.session_state:
        st.session_state.current_q_type = "Çoktan Seçmeli"
    # Her soru için benzersiz id
    if "q_counter" not in st.session_state:
        st.session_state.q_counter = 0
    if "current_q_id" not in st.session_state:
        st.session_state.current_q_id = 0

    colq1, colq2 = st.columns(2)
    with colq1:
        difficulty = st.selectbox("Zorluk seviyesi", ["Temel", "Orta", "İleri"], index=1)
    with colq2:
        qtype = st.selectbox(
            "Soru tipi",
            ["Çoktan Seçmeli", "Doğru/Yanlış", "Vaka Analizi", "Açık Uçlu"],
            index=0
        )
    st.caption("Not: Vaka / Açık uçlu sorularda cevapların değerlendirmesi de AI tarafından yapılır.")

    def _fetch_new_ai_question(api_key, context_text, difficulty, qtype):
        """Yeni soruyu üretip session_state'e yazar; her soru için benzersiz id üretir."""
        if not api_key or not context_text:
            st.warning("API key veya doküman olmadığı için yeni soru üretilemedi.")
            return

        with st.spinner("Soru hazırlanıyor..."):
            q = generate_ai_question(api_key, context_text, difficulty, qtype)
            if q:
                st.session_state.current_q = q
                st.session_state.current_q_difficulty = difficulty
                st.session_state.current_q_type = qtype
                # yeni soru id
                st.session_state.q_counter += 1
                st.session_state.current_q_id = st.session_state.q_counter
            else:
                st.error(
                    "Soru üretilemedi. Muhtemelen Google Gemini kotası dolu "
                    "veya API anahtarında bir sorun var."
                )

    if st.button("🎲 Yeni Soru Getir", key="new_ai_q"):
        _fetch_new_ai_question(api_key, context_text, difficulty, qtype)

    q = st.session_state.current_q
    if q:
        tur = q.get("tur", "coktan_secme")
        st.markdown("#### ❓ Soru")
        st.markdown(q["soru"])

        # Bu soruya özel widget key'leri
        q_id = st.session_state.current_q_id
        radio_key = f"ai_q_radio_{q_id}"
        open_key = f"ai_q_open_{q_id}"

        user_answer_mc = None
        user_answer_open = None

        if tur in ["coktan_secme", "dogru_yanlis"]:
            options = q.get("secenekler") or []
            if not options and tur == "dogru_yanlis":
                options = ["Doğru", "Yanlış"]
            user_answer_mc = st.radio(
                "Cevabın:",
                options,
                key=radio_key
            )
        else:
            user_answer_open = st.text_area(
                "Cevabın (açık uçlu):",
                key=open_key,
                height=200,
                placeholder="Buraya MDR perspektifinden cevabını yaz..."
            )

        if st.button("✅ Cevabı Değerlendir", key="ai_q_check"):
            if not api_key:
                st.error("Değerlendirme için API anahtarı gerekli.")
            else:
                # Çoktan seçmeli / Doğru-Yanlış
                if tur in ["coktan_secme", "dogru_yanlis"]:
                    options = q.get("secenekler") or []
                    if not options and tur == "dogru_yanlis":
                        options = ["Doğru", "Yanlış"]

                    explanation = q.get("aciklama", "")
                    hints = q.get("ipuclari", "")
                    raw_correct = q.get("dogru_cevap", "")
                    canonical_correct = get_canonical_correct_option(q)

                    user_answer_mc = st.session_state.get(radio_key, None)

                    if user_answer_mc is None:
                        st.error("Önce bir şık seçmelisin.")
                    else:
                        if _normalize_text(user_answer_mc) == _normalize_text(canonical_correct):
                            st.success("✅ Doğru cevap!")
                            st.markdown(f"**Açıklama:** {explanation}")
                            if hints:
                                st.info(f"İpucu / Ek Not: {hints}")
                            st.session_state.quiz_score += 10
                        else:
                            st.error(
                                f"❌ Yanlış cevap.\n\n"
                                f"Senin cevabın: **{user_answer_mc}**\n\n"
                                f"Doğru cevap (şık metni): **{canonical_correct}**"
                            )
                            if raw_correct and canonical_correct != raw_correct:
                                st.caption(f"(Modelin 'dogru_cevap' alanı: `{raw_correct}`)")
                            st.markdown(f"**Açıklama:** {explanation}")
                            if hints:
                                st.info(f"İpucu / Ek Not: {hints}")

                        st.caption(f"Toplam skor: {st.session_state.quiz_score} puan")

                        # ✅ Cevaplandıktan sonra otomatik yeni soru getir
                        _fetch_new_ai_question(
                            api_key,
                            context_text,
                            st.session_state.current_q_difficulty,
                            st.session_state.current_q_type,
                        )

                # Açık uçlu / vaka
                else:
                    user_answer_open = st.session_state.get(open_key, "")
                    if not user_answer_open or user_answer_open.strip() == "":
                        st.error("Lütfen önce bir cevap yaz.")
                    else:
                        with st.spinner("Cevabın MDR kapsamında değerlendiriliyor..."):
                            result = grade_open_answer(
                                api_key,
                                q,
                                user_answer_open,
                                st.session_state.current_q_difficulty
                            )
                            if result is None:
                                st.error("Değerlendirme yapılamadı (API hatası).")
                            else:
                                puan = result.get("puan", 0)
                                deger = result.get("degerlendirme", "")
                                eksikler = result.get("eksikler", "")
                                guclu = result.get("guclu_yonler", "")

                                if puan >= 75:
                                    st.success(f"Skor: {puan} / 100 ✅ (Gayet iyi)")
                                elif puan >= 50:
                                    st.warning(f"Skor: {puan} / 100 ⚠️ (Geliştirilebilir)")
                                else:
                                    st.error(f"Skor: {puan} / 100 ❌ (Önemli eksikler var)")

                                st.markdown("**Genel Değerlendirme:**")
                                st.markdown(deger)
                                if guclu:
                                    st.markdown("**Güçlü Yönler:**")
                                    st.markdown(guclu)
                                if eksikler:
                                    st.markdown("**Eksikler / İyileştirme Alanları:**")
                                    st.markdown(eksikler)

                                # ✅ Açık uçlu soru sonrası da yeni soru getir
                                _fetch_new_ai_question(
                                    api_key,
                                    context_text,
                                    st.session_state.current_q_difficulty,
                                    st.session_state.current_q_type,
                                )

# --- TAB 3: ASİSTAN ---
with tab_asistan:
    st.markdown("### 🤖 Akıllı MDR Asistanı (V4.0)")

    if "assistant_mode" not in st.session_state:
        st.session_state.assistant_mode = "Eğitmen Modu"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    colm1, colm2 = st.columns([2, 3])
    with colm1:
        mode = st.selectbox(
            "Asistan Modu",
            ["Eğitmen Modu", "Denetçi Modu", "Teknik Dosya Modu", "Risk Analizi Modu"],
            index=["Eğitmen Modu", "Denetçi Modu", "Teknik Dosya Modu", "Risk Analizi Modu"].index(
                st.session_state.assistant_mode
            ),
        )
        st.session_state.assistant_mode = mode
    with colm2:
        st.info(
            "Seçilen moda göre asistanın tarzı ve odak noktası değişir.\n\n"
            "• Eğitmen: Anlatım ve kavrayış\n"
            "• Denetçi: Eleştirel, NB bakışı\n"
            "• Teknik Dosya: Annex II/III yapısı\n"
            "• Risk Analizi: ISO 14971 & senaryo"
        )
        st.caption(f"Aktif mod: **{st.session_state.assistant_mode}**")

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("MDR ile ilgili sorunuzu / talebinizi yazın..."):
        if not api_key:
            st.error("Önce Google API anahtarını girmen gerekiyor.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analiz ediliyor..."):
                    try:
                        model = get_working_model(api_key)
                        ctx = context_text[:8000] if context_text else ""
                        focus = detect_context_focus(context_text) if context_text else None
                        full_prompt = build_assistant_prompt(
                            st.session_state.assistant_mode,
                            ctx,
                            prompt,
                            focus
                        )
                        res = model.generate_content(full_prompt).text
                        st.write(res)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": res}
                        )
                    except Exception as e:
                        handle_api_error(e)

# --- TAB 4: SANAL DENETÇİ ---
with tab_auditor:
    st.markdown("### 🎭 Sanal Denetim (V5.0)")

    if "audit_hist" not in st.session_state:
        st.session_state.audit_hist = []
    if "audit_scenario" not in st.session_state:
        st.session_state.audit_scenario = list(AUDIT_SCENARIOS.keys())[0]
    if "audit_scenario_desc" not in st.session_state:
        st.session_state.audit_scenario_desc = ""
    if "audit_score" not in st.session_state:
        st.session_state.audit_score = 0
    if "audit_q_count" not in st.session_state:
        st.session_state.audit_q_count = 0
    if "audit_nc_list" not in st.session_state:
        st.session_state.audit_nc_list = []
    if "audit_last_question" not in st.session_state:
        st.session_state.audit_last_question = ""
    if "audit_finished" not in st.session_state:
        st.session_state.audit_finished = False

    col_a1, col_a2 = st.columns([2, 2])
    with col_a1:
        scenario_key = st.selectbox(
            "Denetim Senaryosu",
            list(AUDIT_SCENARIOS.keys()),
            index=list(AUDIT_SCENARIOS.keys()).index(st.session_state.audit_scenario)
        )
        st.session_state.audit_scenario = scenario_key
        st.markdown("#### Senaryo Açıklaması")
        st.markdown(AUDIT_SCENARIOS[scenario_key])
    with col_a2:
        max_q = 5
        total_possible = st.session_state.audit_q_count * 5 if st.session_state.audit_q_count > 0 else 0
        if total_possible > 0:
            avg = st.session_state.audit_score / total_possible * 100
            st.metric("Toplam Skor", f"{st.session_state.audit_score} / {total_possible}", f"{avg:.1f} %")
        else:
            st.metric("Toplam Skor", "0 / 0", "+0.0 %")

        st.markdown("#### Şu ana kadar tespit edilen NC'ler")
        if st.session_state.audit_nc_list:
            for nc in st.session_state.audit_nc_list:
                st.markdown(f"- {nc}")
        else:
            st.caption("Henüz NC tespit edilmedi.")

    if st.button("🚨 Denetimi Başlat / Sıfırla"):
        if not api_key:
            st.error("Önce Google API anahtarını gir.")
        else:
            with st.spinner("Denetim başlatılıyor..."):
                try:
                    question, scenario_desc = start_audit_session(api_key, scenario_key, context_text)
                    st.session_state.audit_hist = []
                    st.session_state.audit_scenario_desc = scenario_desc
                    st.session_state.audit_score = 0
                    st.session_state.audit_q_count = 0
                    st.session_state.audit_nc_list = []
                    st.session_state.audit_last_question = question
                    st.session_state.audit_finished = False
                    st.session_state.audit_hist.append({"role": "assistant", "content": question})
                except Exception as e:
                    handle_api_error(e)

    for msg in st.session_state.audit_hist:
        role = "assistant" if msg["role"] == "assistant" else "user"
        avatar = "👮‍♂️" if role == "assistant" else None
        st.chat_message(role, avatar=avatar).write(msg["content"])

    reply = st.chat_input("Cevabınız...")
    if reply:
        if not api_key:
            st.error("Önce Google API anahtarını gir.")
        elif not st.session_state.audit_last_question:
            st.error("Önce 'Denetimi Başlat' butonuna basarak oturumu başlatmalısın.")
        elif st.session_state.audit_finished:
            st.warning("Bu denetim oturumu tamamlandı. Yeni bir oturum için 'Denetimi Başlat / Sıfırla'ya bas.")
        else:
            st.session_state.audit_hist.append({"role": "user", "content": reply})
            st.chat_message("user").write(reply)

            with st.chat_message("assistant", avatar="👮‍♂️"):
                with st.spinner("Denetçi cevabınızı değerlendiriyor..."):
                    try:
                        result = evaluate_audit_answer(
                            api_key,
                            st.session_state.audit_scenario_desc,
                            st.session_state.audit_last_question,
                            reply
                        )
                        puan = int(result.get("puan", 0))
                        deger = result.get("degerlendirme", "")
                        ncs = result.get("nc_listesi", [])
                        next_q = result.get("sonraki_soru", "").strip()
                        done = bool(result.get("tamamlandi_mi", False))

                        if puan < 0:
                            puan = 0
                        if puan > 5:
                            puan = 5

                        st.session_state.audit_score += puan
                        st.session_state.audit_q_count += 1
                        if ncs:
                            st.session_state.audit_nc_list.extend(ncs)

                        st.markdown(f"**Bu sorudan aldığın puan:** {puan} / 5")
                        st.markdown("**Denetçi Değerlendirmesi:**")
                        st.markdown(deger)

                        if ncs:
                            st.markdown("**Bu cevaptan türetilen NC'ler:**")
                            for nc in ncs:
                                st.markdown(f"- {nc}")

                        total_possible = st.session_state.audit_q_count * 5
                        avg = st.session_state.audit_score / total_possible * 100
                        st.info(f"Şu ana kadarki toplam skorun: {st.session_state.audit_score} / {total_possible} ({avg:.1f} %)")

                        eval_text = (
                            f"Bu sorudan aldığın puan: {puan} / 5\n\n"
                            f"Denetçi değerlendirmesi:\n{deger}\n\n"
                        )
                        if ncs:
                            eval_text += "Tespit edilen NC'ler:\n" + "\n".join(f"- {x}" for x in ncs)
                        st.session_state.audit_hist.append({"role": "assistant", "content": eval_text})

                        max_q = 5
                        if done or not next_q or st.session_state.audit_q_count >= max_q:
                            st.session_state.audit_finished = True
                            st.success(
                                "Denetim oturumu tamamlandı. Yukarıdaki NC listesi ve skor, genel performansını özetliyor."
                            )
                        else:
                            st.session_state.audit_last_question = next_q
                            st.session_state.audit_hist.append({"role": "assistant", "content": next_q})

                    except Exception as e:
                        handle_api_error(e)

# --- TAB 5: DOKÜMAN FABRİKASI ---
with tab_docgen:
    st.markdown("### 📝 Doküman Fabrikası (V6.0)")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
        "📄 Klasik Taslak Doküman",
        "✅ GSPR Matrisi (Annex I)",
        "⚠️ Risk Analizi Tablosu (ISO 14971)"
    ])

    def common_device_inputs(prefix: str = ""):
        d_name = st.text_input(f"{prefix}Cihaz Adı", key=f"{prefix}_name")
        d_desc = st.text_area(
            f"{prefix}Cihaz Tanımı / Intended Purpose Özeti",
            key=f"{prefix}_desc",
            height=120,
            placeholder="Cihazın klinik amacı, kullanıcı profili, kullanım ortamı, temel teknolojisi vb. özetleyin..."
        )
        return d_name, d_desc

    # --- Klasik Taslak Doküman ---
    with sub_tab1:
        st.markdown("Bu bölüm, klasik doküman taslağını üretir.")
        d_name, d_desc = common_device_inputs("classic")
        d_type = st.selectbox("Doküman Tipi", ["PMS Planı", "Risk Analizi", "GSPR"], key="classic_type")

        if st.button("Taslağı Oluştur", key="classic_btn"):
            if not api_key:
                st.error("Önce Google API anahtarını gir.")
            elif not context_text:
                st.error("Bağlam bulunamadı. 'dokumanlar' klasörüne PDF eklediğinden emin ol.")
            else:
                with st.spinner("Yazılıyor..."):
                    try:
                        model = get_working_model(api_key)
                        doc = model.generate_content(
                            f"Cihaz: {d_name}\n"
                            f"Cihaz tanımı: {d_desc}\n"
                            f"Doküman tipi: {d_type}\n\n"
                            f"Bağlam (MDR/ISO):\n{context_text[:3000]}\n\n"
                            "Bu bilgiler ışığında profesyonel, denetime hazır bir taslak doküman yaz. "
                            "Türkçe yaz ve başlıklar/alt başlıklar kullan."
                        ).text
                        st.markdown(doc)
                        st.download_button("İndir", doc, f"{d_name}_{d_type}.txt")
                    except Exception as e:
                        handle_api_error(e)

    # --- GSPR Matrisi ---
    with sub_tab2:
        st.markdown("Bu bölüm, cihazın için örnek bir **GSPR matrisi** (Annex I) taslağı üretir.")
        d_name_g, d_desc_g = common_device_inputs("gspr")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.caption("Çıktı: Annex I maddelerine göre yapılandırılmış kısa GSPR matrisi.")
        with col_g2:
            st.caption("Not: Bu çıktı, gerçek teknik dosya GSPR matrisinin iskeleti olarak düşünülmelidir.")

        if st.button("GSPR Matrisi Oluştur", key="gspr_btn"):
            if not api_key:
                st.error("Önce Google API anahtarını gir.")
            elif not d_name_g or not d_desc_g:
                st.error("Cihaz adı ve tanımını doldurman gerekiyor.")
            else:
                with st.spinner("GSPR matrisi hazırlanıyor..."):
                    try:
                        rows = generate_gspr_matrix(api_key, d_name_g, d_desc_g, context_text)
                        if not isinstance(rows, list) or len(rows) == 0:
                            st.error("GSPR matrisi üretilemedi (boş çıktı).")
                        else:
                            st.session_state.gspr_matrix = rows
                            st.session_state.gspr_device_name = d_name_g

                            st.markdown("#### Örnek GSPR Matrisi")
                            st.table(rows)

                            json_str = json.dumps(rows, indent=2, ensure_ascii=False)
                            st.download_button(
                                "JSON Olarak İndir",
                                json_str.encode("utf-8"),
                                file_name=f"{d_name_g}_GSPR_Matrisi.json"
                            )

                            headers = [
                                "gspr_no", "baslik", "gereklilik_ozeti",
                                "uygulanabilirlik", "uygunluk_gosterimi", "dokuman_referansi"
                            ]
                            csv_lines = [",".join(headers)]
                            for r in rows:
                                line = []
                                for h in headers:
                                    val = str(r.get(h, "")).replace("\n", " ").replace(",", ";")
                                    line.append(val)
                                csv_lines.append(",".join(line))
                            csv_content = "\n".join(csv_lines)
                            st.download_button(
                                "CSV Olarak İndir",
                                csv_content.encode("utf-8"),
                                file_name=f"{d_name_g}_GSPR_Matrisi.csv"
                            )
                    except Exception as e:
                        handle_api_error(e)

    # --- Risk Analizi Tablosu ---
    with sub_tab3:
        st.markdown("Bu bölüm, cihaz için örnek bir **ISO 14971 uyumlu risk analizi tablosu** üretir.")
        d_name_r, d_desc_r = common_device_inputs("risk")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.caption("Çıktı: Hazard → Sequence → Hazardous Situation → Harm zincirine göre riskler.")
        with col_r2:
            st.caption(
                "Not: Bu tablo, kendi risk yönetimi dosyan için başlangıç noktasıdır, doğrudan kopyala-yapıştır değil."
            )

        if st.button("Risk Analizi Tablosu Oluştur", key="risk_btn"):
            if not api_key:
                st.error("Önce Google API anahtarını gir.")
            elif not d_name_r or not d_desc_r:
                st.error("Cihaz adı ve tanımını doldurman gerekiyor.")
            else:
                with st.spinner("Risk analizi tablosu hazırlanıyor..."):
                    try:
                        rows = generate_risk_table(api_key, d_name_r, d_desc_r, context_text)
                        if not isinstance(rows, list) or len(rows) == 0:
                            st.error("Risk analizi tablosu üretilemedi (boş çıktı).")
                        else:
                            st.session_state.risk_table = rows
                            st.session_state.risk_device_name = d_name_r

                            st.markdown("#### Örnek Risk Analizi Tablosu")
                            st.table(rows)

                            json_str = json.dumps(rows, indent=2, ensure_ascii=False)
                            st.download_button(
                                "JSON Olarak İndir",
                                json_str.encode("utf-8"),
                                file_name=f"{d_name_r}_Risk_Analizi.json"
                            )

                            headers = [
                                "hazard", "sequence_of_events", "hazardous_situation",
                                "harm", "initial_severity", "initial_probability",
                                "risk_controls", "residual_severity", "residual_probability",
                                "risk_evaluation"
                            ]
                            csv_lines = [",".join(headers)]
                            for r in rows:
                                line = []
                                for h in headers:
                                    val = str(r.get(h, "")).replace("\n", " ").replace(",", ";")
                                    line.append(val)
                                csv_lines.append(",".join(line))
                            csv_content = "\n".join(csv_lines)
                            st.download_button(
                                "CSV Olarak İndir",
                                csv_content.encode("utf-8"),
                                file_name=f"{d_name_r}_Risk_Analizi.csv"
                            )
                    except Exception as e:
                        handle_api_error(e)

# --- TAB 6: İZLENEBİLİRLİK ---
with tab_trace:
    st.markdown("### 🔗 GSPR – Risk İzlenebilirlik Görünümü (V7.0)")
    st.markdown(
        "Bu bölüm, oluşturduğun **GSPR matrisi** ile **Risk analizi tablosu** arasındaki bağlantıyı "
        "otomatik olarak çıkarır ve basit bir izlenebilirlik matrisi üretir."
    )

    gspr_rows = st.session_state.get("gspr_matrix")
    risk_rows = st.session_state.get("risk_table")
    dev_g = st.session_state.get("gspr_device_name")
    dev_r = st.session_state.get("risk_device_name")

    if not gspr_rows or not risk_rows:
        st.warning(
            "Önce Doküman Fabrikası sekmesinden hem **GSPR Matrisi** hem de **Risk Analizi Tablosu** "
            "oluşturmalısın. Ardından burada otomatik izlenebilirlik alabilirsin."
        )
    else:
        st.info(
            f"Aktif cihaz(lar): "
            f"GSPR için **{dev_g or 'N/A'}**, Risk analizi için **{dev_r or 'N/A'}**. "
            "İdeal olarak aynı cihaz olmalı, ancak eğitim amaçlı farklı cihazlar da analiz edilebilir."
        )
        with st.expander("GSPR Matrisini Göster", expanded=False):
            st.table(gspr_rows)
        with st.expander("Risk Analizi Tablosunu Göster", expanded=False):
            st.table(risk_rows)

        if st.button("🔗 İzlenebilirlik Matrisi Oluştur", key="trace_btn"):
            if not api_key:
                st.error("Önce Google API anahtarını gir.")
            else:
                with st.spinner("GSPR ↔ Risk eşleştirmeleri hesaplanıyor..."):
                    try:
                        trace = generate_traceability_matrix(api_key, gspr_rows, risk_rows)
                        st.session_state.trace_matrix = trace
                    except Exception as e:
                        handle_api_error(e)

        trace = st.session_state.get("trace_matrix")
        if trace:
            st.markdown("#### Oluşturulan İzlenebilirlik Matrisi (Risk → GSPR)")
            display_rows = []
            for item in trace:
                idx = item.get("risk_index", 0)
                risk_ozet = item.get("risk_ozet", "")
                gspr_list_str = ", ".join(item.get("gspr_list", []))
                base_risk = risk_rows[idx] if 0 <= idx < len(risk_rows) else {}
                display_rows.append({
                    "Risk Index": idx,
                    "Hazard": base_risk.get("hazard", ""),
                    "Harm": base_risk.get("harm", ""),
                    "Risk Özeti": risk_ozet,
                    "İlgili GSPR No'lar": gspr_list_str,
                })
            st.table(display_rows)

            json_str = json.dumps(trace, indent=2, ensure_ascii=False)
            st.download_button(
                "İzlenebilirlik Matrisini JSON Olarak İndir",
                json_str.encode("utf-8"),
                file_name="Traceability_Matrix.json"
            )

            headers = ["risk_index", "risk_ozet", "gspr_list"]
            csv_lines = [",".join(headers)]
            for item in trace:
                risk_index = str(item.get("risk_index", 0))
                risk_ozet = str(item.get("risk_ozet", "")).replace("\n", " ").replace(",", ";")
                gspr_list = ";".join(item.get("gspr_list", []))
                csv_lines.append(",".join([risk_index, risk_ozet, gspr_list]))
            csv_content = "\n".join(csv_lines)
            st.download_button(
                "İzlenebilirlik Matrisini CSV Olarak İndir",
                csv_content.encode("utf-8"),
                file_name="Traceability_Matrix.csv"
            )

            st.markdown("#### Kısa Yorum")
            st.caption(
                "- Her risk satırının hangi GSPR maddeleri ile ilişkilendirildiğini görebilirsin.\n"
                "- NB denetiminde, bu matrisi teknik dosyadaki GSPR matrisi ve risk yönetimi dosyası ile "
                "izlenebilirlik kanıtı olarak kullanabilirsin (tabii ki kendi revizyonlarınla)."
            )

# --- TAB 7: CHECKLIST & TEST PLAN (V8.0) ---
with tab_plan:
    st.markdown("### 📋 Denetim Checklisti & Test Planı (V8.0)")
    st.markdown(
        "Bu bölüm, **GSPR matrisi + Risk tablosu + İzlenebilirlik matrisi** üzerinden, "
        "otomatik bir **denetim checklisti** ve **test planı** oluşturur."
    )

    gspr_rows = st.session_state.get("gspr_matrix")
    risk_rows = st.session_state.get("risk_table")
    trace = st.session_state.get("trace_matrix")
    dev_g = st.session_state.get("gspr_device_name") or ""
    dev_r = st.session_state.get("risk_device_name") or ""
    device_name_for_plan = dev_g or dev_r or "Tanımsız Cihaz"

    if not gspr_rows or not risk_rows:
        st.warning("Önce Doküman Fabrikası sekmesinde GSPR matrisi ve Risk tablosu üretmelisin.")
    elif not trace:
        st.warning("Önce 'İzlenebilirlik' sekmesinde bir izlenebilirlik matrisi oluşturmalısın.")
    else:
        st.info(
          f"Checklist/Test Plan cihaz adı: **{device_name_for_plan}**\n\n"
          "Alttaki butona bastığında, izlenebilirlik verisine göre NB denetçisi gözüyle "
          "checklist ve test planı üretilecek."
        )

        if st.button("📋 Checklist & Test Plan Oluştur", key="plan_btn"):
            if not api_key:
                st.error("Önce Google API anahtarını gir.")
            else:
                with st.spinner("Denetim checklisti ve test planı üretiliyor..."):
                    try:
                        data = generate_checklist_and_testplan(
                            api_key,
                            device_name_for_plan,
                            gspr_rows,
                            risk_rows,
                            trace
                        )
                        st.session_state.checklist_plan = data
                    except Exception as e:
                        handle_api_error(e)

        plan_data = st.session_state.get("checklist_plan")
        if plan_data:
            checklist = plan_data.get("denetim_checklist", [])
            test_plan = plan_data.get("test_plan", [])

            st.markdown("#### ✅ Denetim Checklisti")
            if checklist:
                display_rows = []
                for item in checklist:
                    display_rows.append({
                        "Madde": item.get("madde", ""),
                        "Kaynak": item.get("kaynak", ""),
                        "Tip": item.get("tip", ""),
                    })
                st.table(display_rows)

                json_str = json.dumps(checklist, indent=2, ensure_ascii=False)
                st.download_button(
                    "Checklist'i JSON Olarak İndir",
                    json_str.encode("utf-8"),
                    file_name=f"{device_name_for_plan}_Denetim_Checklist.json"
                )

            st.markdown("#### 🧪 Test Planı")
            if test_plan:
                display_rows_t = []
                for t in test_plan:
                    display_rows_t.append({
                        "Test Adı": t.get("test_adi", ""),
                        "Amaç": t.get("amac", ""),
                        "İlgili GSPR": ", ".join(t.get("iliskili_gspr", [])),
                        "İlgili Risk Index": ", ".join(str(x) for x in t.get("iliskili_riskler", [])),
                        "Test Tipi": t.get("test_tipi", ""),
                        "Öncelik": t.get("oncelik", ""),
                    })
                st.table(display_rows_t)

                json_str_t = json.dumps(test_plan, indent=2, ensure_ascii=False)
                st.download_button(
                    "Test Planını JSON Olarak İndir",
                    json_str_t.encode("utf-8"),
                    file_name=f"{device_name_for_plan}_Test_Plan.json"
                )

            if checklist or test_plan:
                st.markdown("#### Kullanım Önerisi")
                st.caption(
                    "- Checklist maddelerini, kendi NB denetim hazırlık listene uyarlayabilirsin.\n"
                    "- Test planı girdilerini, gerçek laboratuvar/validation protokollerine dönüştürerek "
                    "Annex II/III ve ISO 13485 kapsamında kayıt altına alabilirsin."
                )

# --- TAB 8: STOK & PROSES ANALİZİ ---
with tab_stock:
    st.markdown("### 🏭 Stok Listesi Sınıflandırma & İstasyon Talimatları")
    st.markdown(
        "Stok listesini (CSV / Excel) yükle; her ürün için MDR sınıfı tahmini al ve "
        "sayım → kumlama → polisaj → lazer markalama → altın kaplama → yıkama → paketleme → kalite kontrol "
        "istasyonları için operatör kullanım kılavuzu oluştur."
    )

    uploaded_file = st.file_uploader("Stok listeni yükle (CSV / Excel)", type=["csv", "xlsx", "xls"])

    df = None
    if uploaded_file is not None:
        file_name_lower = uploaded_file.name.lower()
        # Dosyayı içeri al
        try:
            if file_name_lower.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif file_name_lower.endswith(".xlsx"):
                # xlsx için openpyxl genelde kurulu olur
                df = pd.read_excel(uploaded_file, engine="openpyxl")
            elif file_name_lower.endswith(".xls"):
                # Eski Excel formatı: xlrd gerektiriyor
                try:
                    df = pd.read_excel(uploaded_file, engine="xlrd")
                except ImportError:
                    st.error(
                        "❗ '.xls' uzantılı dosyalar için 'xlrd' paketi bu ortamda yüklü değil.\n\n"
                        "Lütfen dosyanı Excel'de açıp 'Farklı Kaydet' ile **.xlsx** formatında "
                        "kaydet ve tekrar yükle."
                    )
                    df = None
            else:
                st.error("Desteklenmeyen dosya uzantısı. Lütfen CSV, XLS veya XLSX yükleyin.")
                df = None
        except Exception as e:
            st.error(f"Dosya okunurken beklenmedik bir hata oluştu: {e}")
            df = None

        if df is not None:
            if not df.empty:
                st.markdown("#### Yüklenen Stok Listesi (İlk satırlar)")
                st.dataframe(df.head(50))

                cols = list(df.columns)
                name_col = st.selectbox(
                    "Ürün adı sütunu",
                    cols,
                    index=0,
                    key="stock_name_col"
                )
                desc_col = st.selectbox(
                    "Ürün açıklaması / intended purpose sütunu",
                    cols,
                    index=1 if len(cols) > 1 else 0,
                    key="stock_desc_col"
                )

                max_n = len(df)
                limit = st.number_input(
                    "Maksimum ürün sayısı (API kotasını korumak için)",
                    min_value=1,
                    max_value=max_n,
                    value=min(10, max_n),
                    step=1
                )

                if st.button("Ürünleri Sınıflandır ve İstasyon Talimatlarını Oluştur", key="stock_run_btn"):
                    if not api_key:
                        st.error("Önce Google API anahtarını gir.")
                    else:
                        results = []
                        with st.spinner("Ürünler analiz ediliyor..."):
                            for idx, row in df.head(int(limit)).iterrows():
                                name = str(row.get(name_col, "")).strip()
                                desc = str(row.get(desc_col, "")).strip()
                                if not name:
                                    continue
                                if not desc:
                                    desc = name  # açıklama boşsa en azından isim kullan
                                try:
                                    res = classify_and_build_work_instructions(
                                        api_key,
                                        name,
                                        desc,
                                        context_text
                                    )
                                    res["row_index"] = int(idx)
                                    results.append(res)
                                except Exception as e:
                                    handle_api_error(e)
                                    break

                        if results:
                            st.session_state.stock_analysis_results = results
                            st.success(f"{len(results)} ürün için sınıf ve talimat üretildi.")
                        else:
                            st.warning("Hiçbir ürün için analiz yapılamadı.")
            else:
                st.warning("Dosya boş görünüyor (satır bulunamadı).")

    # Sonuçlar varsa göster
    results = st.session_state.get("stock_analysis_results") if "stock_analysis_results" in st.session_state else None
    if results:
        st.markdown("### 📊 Analiz Sonuçları")

        station_labels = {
            "sayim": "1️⃣ Sayım",
            "kumlama": "2️⃣ Kumlama",
            "polisaj": "3️⃣ Polisaj",
            "lazer_markalama": "4️⃣ Lazer Markalama",
            "altin_kaplama": "5️⃣ Altın Kaplama",
            "yikama": "6️⃣ Yıkama",
            "paketleme": "7️⃣ Paketleme",
            "kalite_kontrol": "8️⃣ Kalite Kontrol",
        }

        for i, item in enumerate(results):
            urun_adi = item.get("urun_adi", f"Ürün {i+1}")
            sinif = item.get("onerilen_sinif", "Belirtilmedi")
            gerekce = item.get("sinif_gerekcesi", "")
            talimatlar = item.get("istasyon_talimatlari", {}) or {}

            with st.expander(f"{i+1}. {urun_adi} — {sinif}", expanded=False):
                st.markdown(f"**Önerilen MDR Sınıfı:** {sinif}")
                if gerekce:
                    st.markdown(f"**Sınıf Gerekçesi:** {gerekce}")

                for key, label in station_labels.items():
                    if key in talimatlar:
                        data = talimatlar.get(key, {})
                        st.markdown(f"##### {label}")
                        amac = data.get("amaç") or data.get("amac", "")
                        if amac:
                            st.markdown(f"**Amaç:** {amac}")
                        kritikler = data.get("kritik_noktalar", [])
                        kayitlar = data.get("kayıtlar", []) or data.get("kayitlar", [])
                        if kritikler:
                            st.markdown("**Kritik Noktalar:**")
                            for k in kritikler:
                                st.markdown(f"- {k}")
                        if kayitlar:
                            st.markdown("**Kayıtlar / Dokümanlar:**")
                            for k in kayitlar:
                                st.markdown(f"- {k}")

        # Toplu JSON indirme
        json_all = json.dumps(results, indent=2, ensure_ascii=False)
        st.download_button(
            "Tüm Sonuçları JSON Olarak İndir",
            json_all.encode("utf-8"),
            file_name="Stok_Proses_Analizi.json",
            key="stock_json_dl"
        )
    else:
        st.caption("Henüz analiz edilmiş stok ürünü yok. Dosya yükleyip butona basarak başlayabilirsin.")
