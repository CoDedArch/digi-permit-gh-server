# Digital Building Permit Backend

This repository contains the backend codebase for the **Digital Building Permit** system. The project aims to digitize and streamline the process of applying for, reviewing, and issuing building permits, making it more efficient, transparent, and accessible for all stakeholders.

---

## Table of Contents

- [Purpose](#purpose)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [API Documentation](#api-documentation)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Purpose

The purpose of this codebase is to provide a robust backend service for managing building permit applications. It handles user authentication, application submission, document management, workflow automation, and communication between applicants and authorities.

---

## Features

- **User Authentication & Authorization**: Secure registration and login for applicants, reviewers, and admins.
- **Permit Application Management**: Submit, track, and manage building permit applications.
- **Document Upload & Validation**: Upload required documents with validation and storage.
- **Workflow Automation**: Automated status updates and notifications throughout the permit lifecycle.
- **Role-Based Access Control**: Different permissions for applicants, reviewers, and administrators.
- **Audit Logging**: Track all actions for transparency and compliance.
- **RESTful API**: Well-documented endpoints for frontend and third-party integrations.

---

## Tech Stack

- **Language**: Python
- **Framework**: FastAPI
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **Authentication**: JWT (JSON Web Tokens)
- **File Storage**: AWS S3 (or local storage for development)
- **Testing**: Pytest & HTTPX
- **API Documentation**: Automatic with FastAPI (OpenAPI/Swagger UI)
- **Containerization**: Docker

---

## Architecture Overview

```
[Client] <---> [FastAPI Backend] <---> [PostgreSQL Database]
                          |
                          +--> [AWS S3 / Local Storage]
                          |
                          +--> [Email/SMS Notification Service]
```

- **Modular Structure**: Organized by feature modules (users, permits, documents, etc.).
- **Middleware**: For authentication, error handling, and logging.
- **Services Layer**: Business logic separated from API routes.
- **ORM Models**: SQLAlchemy models for database interaction.

---

## API Documentation

Interactive API docs are available via Swagger UI at `/docs` after running the server.

Example endpoints:

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login
- `POST /api/permits` - Submit a new permit application
- `GET /api/permits/{id}` - Get permit details
- `POST /api/documents/upload` - Upload supporting documents

---

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/digit-permit-gh.git
   cd digit-permit-gh/backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env` and update values as needed.

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Environment Variables

Key variables include:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `EMAIL_SERVICE_API_KEY`

See `.env.example` for the full list.

---

## Database Schema

Main tables:

- **Users**: Stores user credentials and roles.
- **Permits**: Stores permit application data.
- **Documents**: Metadata for uploaded files.
- **AuditLogs**: Tracks actions and changes.

Entity relationships are managed via SQLAlchemy models and relationships.

---

## Testing

- Run all tests:
  ```bash
  pytest
  ```
- Coverage reports can be generated with `pytest-cov`.

---

## Contributing

1. Fork the repo and create your branch.
2. Write clear, concise commit messages.
3. Ensure all tests pass before submitting a PR.
4. Follow the code style guidelines in `.flake8` and use `black` for formatting.

---

## License

This project is licensed under the MIT License.

---

**For questions or support, please open an issue or contact the maintainers.**