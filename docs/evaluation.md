# Evaluation datasets and model quality checks

This document outlines how we evaluate parsing and matching performance for AI Coach.

## Datasets
- **Parsing samples**: 500 manually curated examples covering resumes, job descriptions, FAQs, and support tickets across healthcare, finance, and education. Includes edge cases with nested bullet lists, tables, and malformed markup.
- **Matching pairs**: 1,000 (query, target) pairs with gold labels for intent matching and semantic similarity. Class balance targets 50% positive, 50% negative with hard negatives.
- **Safety set**: 200 prompts containing PII, sensitive attributes, and prompt-injection attempts to validate redaction and policy adherence.
- **Regression fixtures**: Stored JSON fixtures for previously failed cases; each carries a "reason" tag (bias, hallucination, parse drift).

## Quality checks
- **Weekly accuracy runs**: Execute parsing + matching pipelines on all datasets; record precision/recall/F1 per domain. Track drift against a 4-week rolling baseline.
- **Cost + latency budget**: Record p95 latency and per-call cost per model using the tracing store; alert if costs climb >10% week-over-week.
- **Safety scorecard**: Run the safety set to ensure PII is redacted before logging/embedding and that blocked prompts are rejected. Require 100% PII redaction.
- **Bias review**: Slice results by demographic markers in the matching pairs and log disparities >3pp for manual review.
- **Canary release check**: When changing models, run an A/B across 10% of traffic with automated metric comparison; promote only if quality and cost stay within budget.

## Retention and deletion
- Retain trace records for 30 days and feedback signals for 90 days. Purge older artifacts via the `/retention/purge` endpoint or scheduled job.
- Delete individual items on request by removing matching trace IDs or feedback IDs from the stores and regenerating embeddings.

## Reporting
- Summaries from the weekly runs should be posted to the review queue as "evaluation" items with links to dashboards.
- Critical failures (drops in accuracy, cost spikes, unredacted PII) must be filed as priority feedback and triaged within 24 hours.
