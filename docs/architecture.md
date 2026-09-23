# Adera Architecture

## Core Workflow

Customer Payment
        ↓
Fraud Intelligence
        ↓
Entities & Relationships
        ↓
Risk Engine
        ↓
Risk Assessment
        ↓
Alert
        ↓
Investigation
        ↓
Case
        ↓
Analyst Decision

## System Components

### Frontend

React application used by:

- customers
- analysts

### Backend

FastAPI API connecting:

- frontend
- database
- risk engine
- alerts
- cases

### Database

PostgreSQL stores:

- users
- accounts
- transactions
- fraud reports
- scam cases
- account relationships
- risk assessments
- alerts

### Risk Engine

Rule-based explainable risk scoring.

### Investigation

Analysts can investigate:

- alerts
- accounts
- transactions
- fraud reports
- relationships
- scam cases

### Decisions

Analysts can record:

- FRAUD
- FALSE_POSITIVE
- NEEDS_MORE_INFORMATION

## Data Flow

React
  ↓
FastAPI
  ↓
PostgreSQL
  ↓
Risk Engine
  ↓
Risk Assessment
  ↓
Alert
  ↓
Case
  ↓
Analyst Decision