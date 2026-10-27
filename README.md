# Adera — Digital Payment Fraud Intelligence

## Project Overview

Adera is an Ethiopia-focused fraud-intelligence and investigation platform designed to help identify, report, assess, and investigate suspicious digital-payment activity.

The project demonstrates how fraud reports, suspicious indicators, entity relationships, and explainable risk assessments can help analysts prioritize potential threats and make informed investigation decisions.

Adera can be integrated with cryptocurrency exchanges, travel and accommodation booking platforms, rental platforms, e-commerce websites, and online marketplaces. More broadly, Adera can be integrated into digital payment solutions and digital wallets to enhance transaction security through risk assessment, risk scoring, and explainable warnings for each transaction and recipient. By identifying potential threats in advance and providing actionable insights to guide users' decisions, Adera mitigates the likelihood of financial losses.

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

## Quick Start & Local Setup

- **Development Setup Guide:** See [docs/development-setup.md](docs/development-setup.md) for automated dependency installation (`scripts/setup.sh` / `scripts/setup.ps1`), database setup with Docker Compose, and running backend and frontend services on Linux, macOS, or Windows.
- **Standalone Local Demo:** See [docs/local-demo.md](docs/local-demo.md) to explore the full analyst workflow immediately using an isolated, zero-PostgreSQL SQLite mock environment.

## GitHub Repository

[View the Adera source code](https://github.com/Ahmedmkofficial/adera)

## Team Members

Replace the placeholders below with each member's complete name and verified CTC ID.

No. | Full Name | CTC ID | Contribution |

1. Ahmed Hussen | CTC-1509-26 | Backend development and integration

2. Yoseph Tigiste | CTC-3518-26 | Backend development, integration, and security

3. Biruk Abebe | CTC-3679-26 | Threat intelligence

4. Eyosias Kassu | CTC-2912-26 | Risk engine

5. Reyyan Tesfaye | CTC-2755-26 | Database

6. Yohannes Getachew | CTC-3518-26 | Frontend development

## Disclaimer

Adera is an educational prototype developed to demonstrate fraud-intelligence, risk-assessment, and investigation concepts using synthetic data. Its risk assessments are demonstrative and should not be treated as verified financial or fraud determinations.
