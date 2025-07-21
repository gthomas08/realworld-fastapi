# RealWorld FastAPI

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Poetry](https://img.shields.io/badge/Poetry-%233B82F6.svg?style=for-the-badge&logo=poetry&logoColor=0B3D8D)](https://python-poetry.org/)

![Scalar API Documentation](docs/images/scalar.png)

A modern, production-ready implementation of the [RealWorld specification](https://realworld-docs.netlify.app/) using FastAPI, PostgreSQL, and contemporary Python development practices. This project provides a robust backend API for a Medium-like social blogging platform with comprehensive user authentication, article management, and social features.

While this implementation strives to closely follow the RealWorld specification, there may be minor variations in implementation details to align with FastAPI best practices and modern Python conventions.

## ✨ Features

- 🚀 **FastAPI** - High-performance async API framework
- 🔐 **JWT Authentication** - Secure user authentication with FastAPI Users
- 📚 **Article Management** - Create, read, update, delete articles with tagging
- 💬 **Comments System** - Nested commenting on articles
- 👥 **User Profiles** - Follow/unfollow users and view profiles
- ❤️ **Favorites** - Like and favorite articles
- 🏷️ **Tags** - Organize articles with tags
- 🗄️ **PostgreSQL** - Robust relational database
- 🔄 **Alembic Migrations** - Database schema management
- 🧪 **Comprehensive Testing** - Unit and integration tests with pytest
- 📖 **Interactive API Docs** - Auto-generated OpenAPI documentation

## 🚀 Quick Start

### Option 1: Dev Container (Recommended)

The fastest way to get started is using the provided Dev Container configuration:

1. **Prerequisites**: Install [Docker](https://docker.com) and [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Launch**: Open the project in VS Code and click "Reopen in Container" when prompted, or:
   ```bash
   # Clone the repository
   git clone https://github.com/gthomas08/realworld-fastapi
   cd realworld-fastapi
   
   # Open in VS Code
   code .
   
   # Use Command Palette (Ctrl+Shift+P): "Dev Containers: Reopen in Container"
   ```

3. **Setup database**:
   ```bash
   # Run database migrations
   poetry run alembic upgrade head
   ```

4. **Run the application**:
   ```bash
   # The container automatically installs dependencies
   # Start the development server
   make run
   # Or: poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Scalar docs: http://localhost:8000/scalar

### Option 2: Local Development

If you prefer to run locally without containers:

#### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime environment |
| Poetry | Latest | Dependency management |
| PostgreSQL | 12+ | Database |

#### Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/gthomas08/realworld-fastapi
   cd realworld-fastapi
   
   # Install dependencies
   poetry install
   ```

2. **Database setup**:
   ```bash
   # Create PostgreSQL database
   createdb realworld_fastapi
   
   # Set environment variables
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the server**:
   ```bash
   make run
   ```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost/realworld_fastapi

# Security
SECRET_KEY=your-super-secret-key-here

```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_tags.py

# Run with verbose output
poetry run pytest -v
```

## 🛠️ Development

### Database Migrations

```bash
# Create a new migration
make migrate-autogen name="description_of_change"

# Apply migrations
make migrate-upgrade

# Or using poetry directly:
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

### Code Quality

The project uses modern Python tooling:

```bash
# Format code
poetry run ruff format

# Lint code
poetry run ruff check
```

---

<div align="center">
  <p>Made with ❤️ using FastAPI and modern Python</p>
  <p>
    <a href="https://realworld-docs.netlify.app/">RealWorld</a> •
    <a href="https://fastapi.tiangolo.com/">FastAPI</a> •
    <a href="https://python-poetry.org/">Poetry</a>
  </p>
</div>
