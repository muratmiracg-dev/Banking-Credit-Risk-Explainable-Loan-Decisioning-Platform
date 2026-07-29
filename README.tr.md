# Bankacılık Kredi Riski ve Açıklanabilir Kredi Karar Destek Platformu

[English README](README.md)

Bu proje, kurgusal **Aurelia Bank** için hazırlanmış uçtan uca bir bireysel kredi riski
karar destek sistemidir. 12 aylık temerrüt olasılığı (PD), kredi skoru, A-F risk bandı,
onay / inceleme / ret önerisi, Linear SHAP neden kodları, adalet denetimi ve aylık model
izleme katmanlarını tek bir yönetişim mimarisinde birleştirir.

> [!CAUTION]
> Tüm kayıtlar sentetiktir. Sistem gerçek kredi kararı, fiyatlama, limit tahsisi veya
> olumsuz karar bildirimi için onaylı değildir. Nihai yetki, yetkilendirilmiş insan
> incelemesindedir.

![Kredi riski yönetici kontrol paneli](artifacts/plots/executive_dashboard.png)

## Doğrulanmış sonuçlar

| Gösterge | Sonuç |
|---|---:|
| Sentetik başvuru | 48.000 |
| Geliştirme / doğrulama / zaman dışı test | 29.901 / 6.034 / 12.065 |
| Zaman dışı ROC AUC | **0,738** |
| Gini | **0,475** |
| KS | **0,361** |
| Brier skoru | **0,134** |
| Kalibrasyon eğimi | **0,981** |
| Onay önerisi oranı | **%41,7** |
| Onay önerisi grubunda gözlenen temerrüt | **%7,9** |
| Maksimum aylık skor PSI | **0,017** |
| Maksimum SHAP additivity hatası | **2,66e-15** |

Adalet denetimi cinsiyet gruplarında **1,6 yüzde puan**, yaş gruplarında ise **36,7 yüzde
puan** demografik parite farkı ölçmüştür. Yaş grubu bulgusu
`GOVERNANCE_REVIEW_REQUIRED` olarak açıkça kaydedilmiştir; bu sonuç gizlenmemiş veya
uygun kabul edilmemiştir.

## Proje kapsamı

- Sabit seed ile tekrar üretilebilir sentetik kredi portföyü
- Lojistik regresyon champion ve iki challenger model
- Zaman bazlı geliştirme, doğrulama ve 2025 zaman dışı test
- ROC AUC, Gini, PR AUC, KS, Brier, log loss, kalibrasyon ve risk desilleri
- PD'den kredi skoru, A-F segmenti ve şeffaf karar önerisi
- Log-odds uzayında matematiksel olarak doğrulanan Linear SHAP
- Korunan niteliklerin modelden çıkarılması ve ayrı adalet denetimi
- Aylık performans, PSI ve karar dağılımı izleme
- FastAPI, PostgreSQL, Power BI, Excel, Prometheus/Grafana ve Kubernetes katmanları
- Test, kapsam, CodeQL, pip-audit, Trivy ve Dependabot kontrolleri

## Hızlı başlangıç

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,reporting]"
python scripts/run_pipeline.py
pytest
```

API'yi çalıştırmak için:

```bash
export CREDIT_RISK_ROOT="$PWD"
export CREDIT_RISK_API_KEY="uzun-ve-rastgele-bir-deger"
uvicorn credit_risk.api:app --app-dir src --host 0.0.0.0 --port 8000
```

## Karar politikası

| PD aralığı | Öneri | İnsan incelemesi |
|---|---|---|
| `< %10` | `APPROVE_RECOMMENDATION` | Politika kapsamına göre teyit |
| `%10 - <%22` | `REFER` | Zorunlu |
| `>= %22` | `DECLINE_RECOMMENDATION` | Zorunlu ve bildirim akışı |

Bu çıktılar nihai kredi kararı değildir. Kredi skoru ve risk bandı, sürekli PD değerinin
iletişim katmanlarıdır.

## Profesyonel teslimatlar

- [14 sayfalık formül tabanlı Excel çalışma kitabı](reports/workbook/credit_risk_decision_workbench.xlsx)
- [20 slaytlık yönetici sunumu](reports/presentation/credit_risk_executive_deck.pptx)
- [16 sayfalık model yönetişim raporu](reports/pdf/credit_risk_model_governance_report.pdf)
- [Power BI Project başlangıç paketi](powerbi/CreditRiskDashboard.pbip)
- [Model kartı](docs/governance/model-card.md)
- [Model doğrulama raporu](docs/governance/model-validation-report.md)
- [Adalet değerlendirmesi](docs/governance/fairness-assessment.md)
- [Model izleme runbook'u](docs/operations/monitoring-runbook.md)
- [LinkedIn ve portföy açıklamaları](docs/portfolio/PROJECT_DESCRIPTION.md)

## Sorumluluk sınırı

Proje; Basel kredi riski ilkeleri, EBA kredi kullandırım rehberi, NIST AI RMF, AB AI Act
ve IFRS 9 kavramlarını yalnızca referans eşlemesi olarak kullanır. Mevzuata, muhasebe
standardına veya kurum politikasına uyum iddiası taşımaz.
