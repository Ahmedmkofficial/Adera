# Adera — Digital Payment Fraud Intelligence

## **Project Overview**

Adera is an Ethiopia-focused fraud-intelligence and investigation platform designed to help identify, report, assess, and investigate suspicious digital-payment activity.

The project demonstrates how fraud reports, suspicious indicators, entity relationships, and explainable risk assessments can help analysts prioritize potential threats and make informed investigation decisions.

Adera can be integrated with cryptocurrency exchanges, travel and accommodation booking platforms, rental platforms, e-commerce websites, and online marketplaces. More broadly, Adera can be integrated into digital payment solutions and digital wallets to enhance transaction security through risk assessment, risk scoring, and  explainable warnings for each transaction and recipient. By identifying potential threats in advance and providing actionable insights to guide users' decisions, Adera mitigates the likelihood of financial losses.

**Adera is a prototype that uses synthetic demonstration data. It is not connected to real banking systems or live financial accounts.**

## Key Features

- **Fraud Reporting:** Submit reports about suspected digital-payment scams.
- **Explainable Risk Assessment:** Evaluate suspicious activity and provide reasons behind risk scores.
- **Fraud Intelligence:** Organize scam indicators, entities, and relationships to support investigations.
- **Case Management:** Allow analysts to review reports and explicitly open investigation cases.
- **Analyst Dashboard:** Review cases, alerts, and relevant investigation information.
- **Investigation Workflow:** Support the process from suspicious activity and reporting to risk assessment and analyst review.

## Project Demonstration

**5-Minute Video Presentation:** [Watch the Adera demo](https://drive.google.com/file/d/1JV7X4bqRygCuVJIVkumuTyav-vVeuS7g/view?usp=sharing)

The video demonstrates the project's purpose, main features, and investigation workflow.


## Team Members

| No. | Full Name | CTC ID | Contribution |
|---|---|---|---|
| 1 | Ahmed Hussen | CTC-1509-26 | Backend development and integration |
| 2 | Yoseph Tigiste | CTC-3518-26 | Backend development, integration, and security |
| 3 | Biruk Abebe | CTC-3679-26 | Threat intelligence |
| 4 | Eyosias Kassu | CTC-2912-26 | Risk engine |
| 5 | Reyyan Tesfaye | CTC-2755-26 | Database |
| 6 | Yohannes Getachew | CTC-3395-26 | Frontend development |

## Quick Start & Local Setup

### Docker Quick Start

**Prerequisites:** Git, Docker, and Docker Compose.

#### 1. Clone the repository

```bash
git clone https://github.com/Ahmedmkofficial/Adera.git
cd Adera
```

#### 2. Configure environment variables

Create your environment configuration file:

```bash
cp .env.example .env
```

Open the `.env` file and replace the placeholder `JWT_SECRET_KEY` with a secure random secret.

Generate one using:

```bash
openssl rand -hex 32
```

Copy the generated value into your `.env` file as the `JWT_SECRET_KEY` value.

#### 3. Build and start Adera

Run the following command to build the Docker images and start the application:

```bash
docker compose up --build -d
```

Docker Compose starts the application services, and the backend automatically runs the database migrations.

#### 4. Access Adera

Once the services are running, access the application through:

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

#### 5. Stop the application

To stop the running services, execute:

```bash
docker compose down
```

**Important Notes:**

- Database migrations are executed automatically when the backend starts.
- A fresh Docker installation does not automatically populate the database with demonstration records.
- For the complete pre-populated demonstration experience, follow the Standalone Local Demo guide below.

### Additional Setup Guides

- **Development Setup Guide:** See [docs/development-setup.md](docs/development-setup.md) for automated dependency installation, database setup, and instructions for running the backend and frontend on Linux, macOS, and Windows.

- **Standalone Local Demo:** See [docs/local-demo.md](docs/local-demo.md) to explore the analyst workflow immediately using an isolated SQLite demonstration environment without requiring PostgreSQL.

## **GitHub Repository**

[View the Adera source code](https://github.com/Ahmedmkofficial/Adera)

## Disclaimer

Adera is an educational prototype developed to demonstrate fraud-intelligence, risk-assessment, and investigation concepts using synthetic data. Its risk assessments are demonstrative and should not be treated as verified financial or fraud determinations.
