# Portfolio and LinkedIn copy

## GitHub About

Production-style synthetic credit risk decision-support platform with calibrated PD scoring,
A-F risk bands, exact Linear SHAP, fairness audits, policy simulation, model monitoring,
FastAPI, PostgreSQL, Power BI, Excel and governance documentation.

Suggested topics:

`credit-risk` `credit-scoring` `probability-of-default` `explainable-ai` `shap`
`model-risk-management` `fairness` `mlops` `fastapi` `power-bi`

---

## LinkedIn project description - English

**Banking Credit Risk & Explainable Loan Decisioning Platform**

Designed and delivered a portfolio-grade, end-to-end retail credit risk decision-support
platform for a fictional bank, combining probability of default modeling, transparent credit
policy, explainable AI, fairness diagnostics and model monitoring in one governed architecture.

- Engineered a deterministic synthetic portfolio of **48,000 unsecured loan applications**
  across 2022-2025, with explicit development, validation and out-of-time windows.
- Benchmarked logistic regression, histogram gradient boosting and random forest models;
  selected the interpretable logistic model as champion based on validation performance,
  calibration and auditability.
- Achieved **0.738 OOT ROC AUC**, **0.475 Gini**, **0.361 KS**, **0.134 Brier score** and a
  **0.981 calibration slope** on the 2025 holdout period.
- Translated PD into a governed **300-850 credit score**, A-F risk bands and transparent
  approve / refer / decline recommendations while preserving final human authority.
- Implemented exact additive **Linear SHAP** explanations in log-odds and verified model-output
  reconstruction to a maximum numerical error of **2.66e-15**.
- Isolated protected attributes from training and scoring, then conducted a separate fairness
  audit. A material age-band allocation gap was explicitly escalated as
  `GOVERNANCE_REVIEW_REQUIRED` rather than hidden behind aggregate performance.
- Built monthly monitoring for ROC AUC, Brier, default rate, approval allocation and
  population-stability indices, supported by Prometheus/Grafana operational telemetry.
- Delivered a strict recommendation-only FastAPI service, PostgreSQL analytical layer,
  Power BI Project starter, formula-driven 14-sheet Excel workbench, 20-slide executive deck
  and 16-page model governance report.
- Added CI, reproducibility checks, 90% coverage gate, CodeQL, dependency auditing, container
  scanning, hardened Docker/Kubernetes references and comprehensive model-risk documentation.

**Technology:** Python, pandas, NumPy, scikit-learn, FastAPI, Pydantic, PostgreSQL, SQL,
Power BI Project, DAX/TMDL, Excel, Docker, Kubernetes, Prometheus, Grafana, GitHub Actions,
CodeQL and Trivy.

**Important:** All data and business outcomes are synthetic. The platform is a professional
portfolio demonstration and is not approved for real lending, automated credit decisions or
regulatory reporting.

---

## LinkedIn project description - Turkish

**Banking Credit Risk & Explainable Loan Decisioning Platform**

Kurgusal bir banka için; temerrüt olasılığı modellemesi, şeffaf kredi politikası,
açıklanabilir yapay zekâ, adalet denetimi ve model izleme katmanlarını tek bir yönetişim
mimarisinde birleştiren uçtan uca kredi riski karar destek platformu tasarlandı.

- 2022-2025 dönemini kapsayan **48.000 sentetik teminatsız kredi başvurusu** üretildi ve
  geliştirme, doğrulama ve zaman dışı test dönemleri ayrıldı.
- Lojistik regresyon, histogram gradient boosting ve random forest modelleri karşılaştırıldı;
  performans, kalibrasyon ve denetlenebilirlik birlikte değerlendirilerek lojistik model
  champion seçildi.
- 2025 zaman dışı testinde **0,738 ROC AUC**, **0,475 Gini**, **0,361 KS**, **0,134 Brier**
  ve **0,981 kalibrasyon eğimi** elde edildi.
- PD değerleri 300-850 kredi skoru, A-F risk bandı ve şeffaf onay / inceleme / ret önerisine
  dönüştürüldü; nihai karar yetkisi insan incelemesinde tutuldu.
- Log-odds uzayında exact additive **Linear SHAP** neden kodları geliştirildi ve model çıktısı
  **2,66e-15** maksimum hata ile yeniden doğrulandı.
- Korunan nitelikler modelden tamamen ayrıldı; ayrı adalet denetiminde belirlenen yaş grubu
  tahsis farkı `GOVERNANCE_REVIEW_REQUIRED` olarak açıkça raporlandı.
- ROC AUC, Brier, temerrüt oranı, karar dağılımı ve PSI göstergeleri için aylık model izleme;
  servis sağlığı için Prometheus/Grafana gözlemlenebilirlik katmanı kuruldu.
- FastAPI, PostgreSQL, Power BI, formül tabanlı 14 sayfalık Excel çalışma kitabı, 20 slaytlık
  yönetici sunumu ve 16 sayfalık model yönetişim raporu teslim edildi.
- CI, yeniden üretilebilirlik, test kapsamı, CodeQL, bağımlılık denetimi, container taraması ve
  sertleştirilmiş Docker/Kubernetes örnekleri eklendi.

**Teknoloji:** Python, pandas, NumPy, scikit-learn, FastAPI, Pydantic, PostgreSQL, SQL,
Power BI, DAX/TMDL, Excel, Docker, Kubernetes, Prometheus, Grafana ve GitHub Actions.

**Not:** Tüm veri ve iş sonuçları sentetiktir. Proje gerçek kredi kararı, otomatik onay/ret veya
mevzuat raporlaması için onaylı değildir.

---

## LinkedIn post - English

**New Portfolio Project: Banking Credit Risk & Explainable Loan Decisioning Platform**

Credit risk modeling becomes far more valuable when the probability estimate is connected to
policy, explanation, monitoring and accountable human action. This project was built around
that full decision chain.

The platform includes:

- 48,000 deterministic synthetic loan applications
- temporal development, validation and 2025 out-of-time testing
- logistic-regression champion plus two challenger models
- calibrated 12-month PD, 300-850 score and A-F risk bands
- transparent approve / refer / decline recommendations
- exact additive Linear SHAP reason codes
- protected-group fairness and performance diagnostics
- monthly model-performance and PSI monitoring
- FastAPI, PostgreSQL, Power BI, Excel, Prometheus/Grafana and Kubernetes layers
- complete model card, validation report, risk register and incident runbook

Key OOT results: **ROC AUC 0.738 | Gini 0.475 | KS 0.361 | calibration slope 0.981**.

One result matters just as much as the performance metrics: the fairness audit found a
material age-band allocation gap. The project records this as a governance blocker instead of
presenting the model as “fair” because protected attributes were excluded. That distinction is
central to responsible credit analytics.

All data are synthetic, and the system is recommendation-only. It is not approved for real
lending or automated decisions.

#CreditRisk #CreditScoring #ExplainableAI #SHAP #ModelRiskManagement #ResponsibleAI
#MLOps #FastAPI #PowerBI #DataScience #BankingAnalytics

---

## CV / resume bullets

- Built a deterministic 48,000-application retail credit risk platform with temporal validation,
  calibrated PD scoring and champion/challenger governance; achieved 0.738 OOT ROC AUC and
  0.981 calibration slope.
- Implemented exact additive Linear SHAP reason codes with a 2.66e-15 reconstruction error,
  protected-feature exclusion and disaggregated fairness diagnostics.
- Designed a human-in-the-loop policy layer translating PD into 300-850 scores, A-F risk bands,
  recommendations and illustrative expected loss.
- Delivered FastAPI, PostgreSQL, Power BI, Excel, Docker/Kubernetes, Prometheus/Grafana and
  GitHub Actions components with model cards, validation, monitoring and incident controls.

## Short portfolio summary

An end-to-end synthetic banking decision-support case study demonstrating how credit risk
modeling, explainability, fairness, policy, monitoring and platform engineering can be governed
as one system. The strongest feature is not a single metric; it is the explicit separation of
model recommendation, policy ownership and human decision authority.

## Interview talk track

1. **Business problem:** connect PD estimation to a transparent, reviewable lending workflow.
2. **Data design:** deterministic synthetic portfolio and temporal split to prevent random
   holdout optimism.
3. **Model choice:** logistic regression beat both challengers and supported exact explanations.
4. **Decision policy:** thresholds are configurable and owned separately from the model.
5. **Explainability:** contributions reconstruct log-odds exactly but remain non-causal.
6. **Fairness:** protected fields are excluded, yet age-band allocation still raises a material
   proxy/pathway question.
7. **Monitoring:** performance, calibration, drift and allocation all have owners and triggers.
8. **Engineering:** recommendation-only API, governed SQL/BI, hardened runtime and CI security.
9. **Limitation:** synthetic evidence does not establish real-world validity or compliance.
10. **Next step:** independent validation, fairness investigation, legal/policy review and a
    no-action shadow pilot.
