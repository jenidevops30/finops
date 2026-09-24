# Phase 1 — Project Foundation

This phase adds a clean foundation layer to the existing repository without expanding the existing AWS execution surface.

## Delivered

- src/finops_platform package boundary.
- Validated environment configuration.
- Conservative application logging.
- Pydantic normalized domain models for resources, costs, utilization, findings, and governance findings.
- Finding lifecycle and explicit impact classification.
- Read-only AWS client factory for future collectors.
- Streamlit foundation entry point.
- Pytest configuration and initial model/configuration tests.
- Packaging and CI quality configuration.

## Intentionally deferred

- AWS collectors.
- Cost, utilization, waste, and anomaly analysis.
- Recommendation generation.
- Governance evaluation.
- Persistence.
- Production dashboards.
- Docker.
- GenAI.

## Existing repository note

The repository contains a legacy bot/backend/frontend implementation with execution-oriented code paths. This phase does not silently remove or rewrite those components. Before Phase 2, the legacy execution surface should be reconciled with the new project requirement that the platform remain read-only.

## Safety boundary

The new foundation exposes no terminate, resize, delete, tag, networking, or other AWS mutation operation. Future collectors should be limited to the AWS read permissions required by the data-source specification.
