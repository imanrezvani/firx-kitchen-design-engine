# FirX AI — AI-Powered Kitchen Design Engine

FirX AI is an intelligent kitchen-design platform built around a **parametric kitchen model as the single source of truth**. The system is designed to turn a kitchen design into structured, production-ready information while using AI for design assistance and visualization.

## What FirX Does

FirX connects the design process with manufacturing-oriented outputs:

**Parametric Kitchen Model → Derived Components → BOM → Hardware → Cut List → Materials → Cost → Cabinet Numbering → Technical Drawings → AI Visualization**

The goal is to make kitchen design more consistent, editable, manufacturable, and easier to analyze.

## Core Capabilities

- Parametric kitchen and cabinet modeling
- Cabinet/component derivation from a central design model
- Bill of Materials (BOM)
- Hardware calculation
- Cut-list generation
- Material and cost calculation
- Quote generation
- Cabinet numbering
- Technical drawing and DXF-related tooling
- Kitchen layout editing with spatial interaction
- Image/photo upload for design workflows
- AI-assisted kitchen design and visualization
- Multiple AI providers, including Mock, GPT, and Gemini workflows
- Responsive web interface with light/dark modes

## Architecture Principle

The most important architectural principle is maintaining a **single parametric source of truth** for the kitchen design.

Derived production information should be generated from that model rather than maintained independently. This helps keep BOMs, hardware, cut lists, costs, drawings, and AI prompts synchronized when a design changes.

## Project Structure

```text
.
├── backend/              # Backend API and domain logic
│   ├── app/
│   │   ├── bom/          # BOM, hardware, costing, quotes
│   │   └── design/       # Parametric design and derived outputs
│   └── tests/             # Backend tests
│
├── kitchen-design/       # Kitchen-design research, utilities and assets
├── docs/                 # Architecture, development and reverse-engineering docs
└── frontend/             # Web application (when present in the current checkout)
```

## Development Status

FirX is under active development. The repository contains the current working implementation, supporting tests, documentation, design utilities, and AI pipeline components.

The project is being developed as an independent repository so development can continue independently of any particular coding environment.

## Technology Direction

The project uses a modern web application architecture with a Python backend and a React/Next.js-oriented frontend, together with AI provider integrations and structured design/domain logic.

## Repository Safety

Local runtime data, databases, credentials, environment files, and other sensitive/generated artifacts are intentionally excluded from version control through `.gitignore` rules.

## Vision

FirX aims to become a production-oriented **AI kitchen design and manufacturing intelligence platform**: not simply a visual kitchen configurator, but a system where a design can move toward engineering, costing, documentation, and manufacturing outputs from one consistent parametric model.

---

**Project:** FirX AI  
**Repository:** `imanrezvani/Ai-based-kitchen-design-engine`
