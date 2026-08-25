# 🚀 Advanced FinOps Platform

An **enterprise-grade AWS Cloud Financial Operations (FinOps) platform** that scans your AWS infrastructure, identifies cost-saving opportunities using ML, detects spending anomalies, and surfaces everything through a real-time React dashboard.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Advanced FinOps Platform is a 3-tier system:

| Tier | Component | Role |
|------|-----------|------|
| **Data** | Python Bot (`bot/`) | Scans AWS, runs ML analysis, syncs to backend |
| **API** | Node.js Backend (`backend/`) | REST API — stores and serves FinOps data |
| **UI** | React Frontend (`frontend/`) | Dashboard — visualises costs, anomalies, savings |

**Before vs After:**
```
❌ Before: Frontend → Backend API → Returns [] → Shows MOCK data
✅ After:  AWS → Python Bot → Backend API → Frontend → Real data
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
│         EC2 · RDS · S3 · Lambda · EBS · ELB · CloudWatch   │
└────────────────────────┬────────────────────────────────────┘
                         │  boto3
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 bot/  (Python Engine)                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│  │ AWS      │  │ Core     │  │ ML        │  │ Backend  │  │
│  │ Scanners │→ │ Engines  │→ │ Rightsizing│→ │ Sync     │  │
│  └──────────┘  └──────────┘  └───────────┘  └──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP POST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              backend/  (Node.js / Express 5)                │
│  Resources · Optimizations · Anomalies · Budgets · Savings  │
│                      localhost:5000                         │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP GET (proxy)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              frontend/  (React 18 + Tailwind)               │
│  Dashboard · Resources · Optimizations · Anomalies          │
│  Budgets · Savings · Settings                               │
│                      localhost:3000                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 🔍 AWS Scanning
- **EC2** — idle instance detection, utilisation analysis
- **RDS** — underutilised databases, connection tracking
- **S3** — storage class optimisation, lifecycle policies
- **Lambda** — memory rightsizing, cold-start analysis
- **EBS** — unattached volumes, IOPS utilisation
- **ELB** — idle load balancers, target utilisation
- **CloudWatch** — metric analysis, alarm evaluation

### 🤖 ML & Analytics
- **ML Rightsizing** — scikit-learn models recommend optimal instance sizes
- **Anomaly Detection** — statistical + ML-based cost spike detection (50%+ threshold)
- **Budget Forecasting** — 6-month ahead forecasting at 95% confidence
- **Pricing Intelligence** — Spot vs Reserved Instance vs Savings Plans analysis
- **Cost Allocation** — tag-based team/project cost attribution

### 🛡️ Safety & Governance
- **Dry-run mode** — simulate all changes before applying
- **Approval workflow** — human-in-the-loop gate for medium/high-risk changes
- **Rollback support** — 30-minute rollback window for all operations
- **Risk classification** — LOW / MEDIUM / HIGH / CRITICAL risk levels

### 📊 Dashboard
- Real-time cost metrics and trends
- Interactive charts (Recharts)
- Cost anomaly timeline
- Budget vs actual comparison
- Savings tracker
- Resource inventory

### 🔄 Automation
- Continuous monitoring mode (configurable interval)
- Cron-compatible one-shot sync
- Systemd service support
- Slack / Email / SNS notifications (configurable)

---

## Project Structure

```
finops/
├── bot/                          # Python Automation Engine
│   ├── main.py                   # CLI entry point
│   ├── config.yaml               # Platform configuration
│   ├── requirements.txt          # Python dependencies
│   ├── aws/                      # AWS service clients & scanners
│   │   ├── scan_ec2.py
│   │   ├── scan_rds.py
│   │   ├── scan_s3.py
│   │   ├── scan_ebs.py
│   │   ├── scan_lambda.py
│   │   ├── scan_elb.py
│   │   ├── scan_cloudwatch.py
│   │   ├── cost_explorer.py
│   │   ├── billing_client.py
│   │   └── pricing_client.py
│   ├── core/                     # Business logic & ML engines
│   │   ├── cost_optimizer.py
│   │   ├── anomaly_detector.py
│   │   ├── ml_rightsizing.py     # ML-based rightsizing
│   │   ├── budget_manager.py
│   │   ├── cost_allocation.py
│   │   ├── pricing_intelligence.py
│   │   ├── reporting_engine.py
│   │   ├── execution_engine.py
│   │   └── approval_workflow.py
│   ├── integration/              # Backend sync
│   │   └── backend_sync.py
│   ├── utils/                    # Shared utilities
│   └── tests/                    # pytest test suite
│
├── backend/                      # Node.js REST API
│   ├── server.js                 # Express app entry point
│   ├── routes/                   # API route handlers
│   │   ├── resources.js          # GET/POST /api/resources
│   │   ├── optimizations.js      # GET/POST /api/optimizations
│   │   ├── anomalies.js          # GET/POST /api/anomalies
│   │   ├── budgets.js            # GET/POST /api/budgets
│   │   ├── savings.js            # GET/POST /api/savings
│   │   ├── dashboard.js          # GET /api/dashboard/*
│   │   ├── integration.js        # POST /api/integration/sync
│   │   └── pricing.js            # GET /api/pricing
│   ├── models/                   # Data model definitions
│   │   ├── ResourceInventory.js
│   │   ├── CostOptimization.js
│   │   ├── CostAnomaly.js
│   │   └── BudgetForecast.js
│   └── package.json
│
├── frontend/                     # React Dashboard
│   ├── src/
│   │   ├── App.js
│   │   ├── pages/
│   │   │   ├── Dashboard.js
│   │   │   ├── Resources.js
│   │   │   ├── Optimizations.js
│   │   │   ├── Anomalies.js
│   │   │   ├── Budgets.js
│   │   │   ├── Savings.js
│   │   │   └── Settings.js
│   │   ├── components/
│   │   │   ├── Layout.js
│   │   │   ├── MetricCard.js
│   │   │   ├── StatusBadge.js
│   │   │   └── LoadingSpinner.js
│   │   └── services/             # API client layer
│   └── package.json
│
├── README.md                     # This file
├── README_INTEGRATION.md         # AWS integration guide
├── DATA_FLOW_ANALYSIS.md         # Data flow documentation
└── INTEGRATION_SUMMARY.md        # Integration implementation notes
```

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | ≥ 18.x | Backend & Frontend |
| Python | ≥ 3.9 | Bot engine |
| AWS CLI | ≥ 2.x | AWS credentials |
| npm | ≥ 9.x | Package management |
| pip | ≥ 23.x | Python packages |

**AWS Permissions required:**
- `ec2:Describe*`, `rds:Describe*`, `s3:List*`, `s3:GetBucketMetrics*`
- `lambda:List*`, `elasticloadbalancing:Describe*`
- `cloudwatch:GetMetricStatistics`, `ce:GetCostAndUsage`
- `budgets:ViewBudget`, `pricing:GetProducts`

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd finops

# Backend
cd backend && npm install && cd ..

# Frontend
cd frontend && npm install && cd ..

# Bot (venv lives at project root)
python3 -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
cd bot && pip install -r requirements.txt && cd ..
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter: AWS Access Key ID, Secret, Region (e.g. us-east-1), output format (json)
```

Or via environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Start the Backend

```bash
cd backend
npm run dev         # Development (auto-reload)
# npm start         # Production
```

Backend runs at **http://localhost:5000**

### 4. Start the Frontend

```bash
cd frontend
npm start           # Development server
```

Dashboard at **http://localhost:3000**

### 5. Scan AWS & Sync Data

```bash
cd bot
source ../.venv/bin/activate

# Safe first run (dry-run = no changes applied)
python3 main.py --scan-only --sync-backend --dry-run
```

✅ Your dashboard now shows real AWS data!

---

## Configuration

All bot behaviour is controlled via [`bot/config.yaml`](bot/config.yaml):

| Section | Key Settings |
|---------|-------------|
| `aws.regions` | Regions to scan (default: `us-east-1`, `us-west-2`) |
| `services.enabled` | Which AWS services to scan |
| `services.thresholds.*` | CPU/memory/idle thresholds per service |
| `optimization.ml_rightsizing` | ML confidence & data point requirements |
| `anomaly_detection.thresholds` | Spike % and absolute dollar thresholds |
| `budget_management.forecasting` | Forecast horizon & confidence level |
| `backend_api.base_url` | Backend URL (default: `http://localhost:5000`) |
| `safety.dry_run.default` | Set `true` to always use dry-run mode |
| `notifications` | Email / Slack / SNS alert config |

---

## Usage

### Bot CLI Reference

```bash
cd bot && source ../.venv/bin/activate

# Test AWS & backend connectivity
python3 main.py --test-connection

# Scan all services (no changes, no sync)
python3 main.py --scan-only --dry-run

# Scan & push data to backend
python3 main.py --scan-only --sync-backend

# Full workflow (scan + optimise + sync), dry-run safe
python3 main.py --sync-backend --dry-run

# Scan specific services only
python3 main.py --scan-only --sync-backend --services ec2,rds,lambda

# Continuous monitoring (every 60 minutes)
python3 main.py --continuous --sync-backend --interval 60

# Custom backend URL
python3 main.py --scan-only --sync-backend --backend-url http://api.example.com:5000
```

### Automation: Cron Job

```bash
# Hourly sync (add to crontab)
0 * * * * cd /path/to/finops/bot && ../.venv/bin/python3 main.py --scan-only --sync-backend --dry-run
```

### Automation: Systemd Service

See [`bot/AWS_INTEGRATION_GUIDE.md`](bot/AWS_INTEGRATION_GUIDE.md) for the full systemd unit file.

---

## API Reference

The backend exposes a REST API at `http://localhost:5000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/resources` | AWS resource inventory |
| `POST` | `/api/resources` | Sync resources from bot |
| `GET` | `/api/optimizations` | Cost optimization recommendations |
| `GET` | `/api/anomalies` | Detected cost anomalies |
| `GET` | `/api/budgets` | Budget status & forecasts |
| `GET` | `/api/savings` | Realized savings records |
| `GET` | `/api/dashboard` | Aggregated dashboard data |
| `GET` | `/api/dashboard/metrics` | Key metrics |
| `GET` | `/api/dashboard/charts` | Chart data |
| `POST` | `/api/integration/sync` | Full data sync from bot |
| `GET` | `/api/sync/status` | Last sync status & timestamp |
| `GET` | `/api/pricing` | Pricing intelligence data |

---

## Testing

### Backend Tests

```bash
cd backend

npm test                    # All tests
npm run test:coverage       # With coverage report
npm run test:verbose        # Verbose output
npm run test:routes         # Route tests only
npm run test:validation     # Validation tests only
npm run test:performance    # Performance tests only
```

### Bot Tests

```bash
cd bot
source .venv/bin/activate

pytest tests/               # All tests
pytest tests/ -v            # Verbose
pytest tests/ --cov         # With coverage
```

### Integration Test

```bash
cd bot
python test_integration.py
```

---

## Troubleshooting

### Backend won't start
```bash
cd backend && npm install
curl http://localhost:5000/health
```

### AWS connection fails
```bash
aws sts get-caller-identity   # Verify credentials
aws configure list            # Check config
```

### No data in frontend
```bash
# 1. Check backend has data
curl http://localhost:5000/api/resources

# 2. Re-sync from bot
cd bot && python main.py --scan-only --sync-backend

# 3. Clear browser cache and reload
```

### Bot import errors
```bash
cd bot
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Bot** | Python 3.9+, boto3, scikit-learn, numpy, pandas, scipy, PyYAML, requests |
| **Backend** | Node.js, Express 5, axios, cors, uuid, winston, ws, morgan |
| **Frontend** | React 18, React Router 6, Recharts, Tailwind CSS, Lucide React, axios |
| **Testing** | Jest, Supertest, fast-check, pytest, moto, hypothesis |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests: `npm test` (backend) / `pytest` (bot)
4. Commit with a descriptive message
5. Open a Pull Request

---

## License

ISC License — see individual `package.json` files for details.
