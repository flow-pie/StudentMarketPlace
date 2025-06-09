# 🎓 StudentMarketPlace: Campus Buy & Sell Platform
## 🌐 API Access

The API is live and accessible here:

👉 [`marketplace-api-bjdwhhdbgnauhgac.canadacentral-01.azurewebsites.net`](marketplace-api-bjdwhhdbgnauhgac.canadacentral-01.azurewebsites.net)

PLEASE NOTE:
> 
> ⚠️ This is a pre-release version (`v0.1.0-beta`)
> 
> ⚠️ URL may change in future production deployments

```mermaid
graph TD
    A[StudentMarketPlace] --> B[Core Features]
    A --> C[Tech Stack]
    A --> D[Architecture]
    A --> E[Deployment]
    style A fill:#4e89ae,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#ed6663,stroke:#333
    style C fill:#ffa372,stroke:#333
    style D fill:#44a1a0,stroke:#333
    style E fill:#ffd166,stroke:#333
```

## 🌟 Project Overview

**StudentMarketPlace** is a university-focused marketplace platform that enables students to buy, sell, and trade items
within their campus community. Built with modern security practices and a scalable architecture, this platform helps
students save money while promoting sustainability through reuse of textbooks, electronics, furniture, and other campus
essentials.

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3-green?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/PostgreSQL-14+-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/JWT-Auth-orange?logo=jsonwebtokens" alt="JWT Auth">
  <img src="https://img.shields.io/badge/Docker-Containers-blue?logo=docker" alt="Docker">
</div>

## ✨ Key Features

### 🛍️ Marketplace Essentials
## 🧠 System Call Graph

This diagram gives a quick overview of how different parts of the system interact:

![Student Market Place Call Graph](MartketPlaceCallGraph.drawio.svg)

---

- **📋 Smart Listings** - Create listings with rich descriptions, multiple images, and category tagging
- **🔍 Intelligent Search** - Filter by price range, condition, category, and campus proximity
- **📬 In-App Messaging** - Secure communication between buyers and sellers
- **📊 Analytics Dashboard** - Real-time insights for administrators
- **🔐 Auth System** - JWT-based authentication with password recovery

### 🛡️ Security Framework

```mermaid
graph LR
    A[User] --> B[JWT Auth]
    B --> C[RBAC]
    C --> D[API Validation]
    D --> E[Rate Limiting]
    E --> F[Encrypted Storage]
```

- Role-Based Access Control (RBAC)
- JWT token revocation system
- Input validation for all API endpoints
- Rate limiting and brute-force protection
- Secure password storage with bcrypt

---

## 🧩 Technology Stack

### 🏗️ Backend Architecture

```mermaid
graph LR
    A[Flask] --> B[SQLAlchemy ORM]
    A --> C[Marshmallow Schemas]
    A --> D[Flask-JWT-Extended]
    A --> E[Flask-RESTful]
    B --> F[PostgreSQL]
    D --> G[Redis Token Blocklist]
    style A fill:#44a1a0,stroke:#333
    style B fill:#ffa372,stroke:#333
    style C fill:#ed6663,stroke:#333
    style D fill:#ffd166,stroke:#333
    style E fill:#4e89ae,stroke:#333
```

**Core Components:**

- **Python 3.11+** - Primary backend language
- **Flask** - Lightweight web framework
- **SQLAlchemy** - Database ORM and migration management
- **PostgreSQL** - Primary relational database
- **Redis** - Token revocation store and caching
- **Docker** - Containerization for consistent environments

### 📦 Project Structure

```bash
📦 API-Core/
├── 📁 app/
│   ├── 📁 blueprints/          # 📦 Modular route groups
│   │   ├── 📁 auth/            # 🔐 Auth routes
│   │   ├── 📁 items/           # 🛒 Item listing routes
│   │   └── 📁 messages/        # 💬 Messaging routes
│   ├── 📁 schemas/             # 📜 Marshmallow schemas (validation)
│   ├── 📁 services/            # 🧠 Business logic layer
│   ├── 📁 models/              # 🗄️ SQLAlchemy models
│   ├── 📄 extensions.py        # 🔌 Init db, jwt, cors
│   └── 📄 __init__.py          # 🛠️ create_app() factory
├── 📁 infra/
│   ├── 📄 docker-compose.yml   # 🐳 Docker services config
│   └── 📄 nginx.conf           # 🌐 Reverse proxy config
├── 📁 postman/
│   └── 📄 MarketplaceAPI.postman_collection.json  # 📬 API collection for testing
├── 📄 run.py                   # 🚀 App runner
└── 📄 requirements.txt         # 📦 Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

```bash
📦 Required Tools
├── 🐍 Python 3.11+
├── 🐘 PostgreSQL 14+
├── 🧠 Redis 6+
├── 🐳 Docker 20.10+
└── 📦 Node.js 18+ (for frontend)
```

### Installation

```bash
# Clone the repository
git clone https://github.com/Flow-Pie/StudentMarketPlace.git
cd StudentMarketPlace

# Set up backend environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### Configuration

Create `.env` file with:

```env
# 🌐 Application Settings
APP_ENV=development
DEBUG=True

# 🗄️ Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=marketplace
DB_USER=marketplace_user
DB_PASSWORD=secure_password

# 🔐 JWT Configuration
JWT_SECRET_KEY=your_secure_secret_here
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# 🧠 Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### Running the Application

```bash
# Initialize database
flask db upgrade

# Start backend server
flask run --host=0.0.0.0 --port=5000

# Start Redis service
docker run -d -p 6379:6379 redis:alpine
```

---

## 🧪 Testing & Quality

### 🧪 Testing Strategy

```mermaid
graph TD
    A[Testing Pyramid] --> B1[Unit Tests: 60%]
    A --> B2[Integration Tests: 30%]
    A --> B3[E2E Tests: 10%]
```

### Test Execution

```bash
# Run Python tests with coverage
pytest --cov=app --cov-report=html

# Run security scans
bandit -r app
safety check

# Generate code quality report
flake8 app
```

### Quality Tools

```bash
🔍 Code Linters
├── Flake8 (Python)
├── ESLint (JavaScript)
└── MarkdownLint (Documentation)

🎨 Code Formatters
├── Black (Python)
└── Prettier (Frontend)

🛡️ Security Scanners
├── Bandit
└── Safety
```

---

## 🌐 API Documentation

Explore our interactive API documentation at `http://localhost:5000/` after starting the server.

### Sample Endpoints

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "student@university.edu",
  "password": "securePassword123!"
}
```

```http
GET /api/items?category=BOOKS&min_price=10&max_price=50
Authorization: Bearer <access_token>
```

### Error Handling
```mermaid
sequenceDiagram
    Client->>API: POST /items/123/images (invalid token)
    API->>Client: 401 Unauthorized (TOKEN_INVALID)
    Client->>API: POST /items/123/images (valid token)
    API->>DB: Check item ownership
    DB->>API: Item belongs to user B
    API->>Client: 403 Forbidden (PERMISSION_DENIED)
```

---

## 🚢 Deployment

### Docker Setup

```dockerfile
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: flask run --host=0.0.0.0 --port=5000
    volumes:
      - .:/app
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: marketplace
      POSTGRES_USER: marketplace_user
      POSTGRES_PASSWORD: db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6

volumes:
  postgres_data:
```

### Cloud Deployment

```bash
# Deploy to Heroku
heroku create
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
git push heroku main

# Deploy to AWS ECS
ecs-cli configure --cluster marketplace-cluster
ecs-cli compose --project-name marketplace service up
```

---

## 🤝 Contributing

```markdown
# 🚀 Contributing Guide

*Crafting Excellence in Our Second-Hand Marketplace API*

+ 🌟 First time contributor? Start with "Good First Issue" tasks!

- ‼️ Never push to main/dev directly 
```

```mermaid
graph TD
    A[GitHub Issue] --> B[Create Branch from DEV]
    B --> C[Feature Work]
    B --> D[Hotfix Work]
    C --> E[Open PR → DEV]
    D --> E
    E --> F[Code Review]
    F --> G[CI/CD Pipeline]
    G --> H[QA Testing]
    H --> I[PROD]
```

### Branch Strategy

| Label Type   | Branch Format           | Example                      |
|--------------|-------------------------|------------------------------|
| `Feature`    | `feature/[LABEL]-desc`  | `feature/auction-bid-system` |
| `Bug`        | `hotfix/[LABEL]-issue`  | `hotfix/user-auth-401`       |
| `Experiment` | `spike/[LABEL]-poc`     | `spike/redis-caching`        |
| `Refactor`   | `refactor/[LABEL]-area` | `refactor/item-search`       |

### Commit Guidelines

```bash
git commit -m "feat(notifications): ✨ add push notification service" -m "
- Integrated Firebase Cloud Messaging
- Added rate limiting
- Created documentation in /docs/notifications.md
"
```

| Emoji | Type     | Description                |
|-------|----------|----------------------------|
| ✨     | feat     | New feature                |
| 🐛    | fix      | Bug fix                    |
| 📚    | docs     | Documentation improvements |
| 🚀    | perf     | Performance optimization   |
| 🔒    | security | Security-related changes   |

---

## 📜 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

📬 Contact Options
├── ✉️ Email: startabase@gmail.com
├── 💬 Slack: #student-marketplace-support
└── 🐞 GitHub Issues:  [GitHub Issues](https://github.com/Flow-Pie/StudentMarketPlace/issues)

```bash
📬 Contact Options
├── ✉️ Email: startabase@gmail.com
├── 💬 Slack: #student-marketplace-support
└── 🐞 GitHub Issues
```

<div align="center">
  <br>
  <img src="https://img.shields.io/github/issues/Flow-Pie/StudentMarketPlace" alt="GitHub issues">
  <img src="https://img.shields.io/github/forks/Flow-Pie/StudentMarketPlace" alt="GitHub forks">
  <img src="https://img.shields.io/github/stars/Flow-Pie/StudentMarketPlace" alt="GitHub stars">
  <br><br>
  <h3>👨‍💻 Happy Trading!</h3>
  <p>The StudentMarketPlace Team</p>
</div>
