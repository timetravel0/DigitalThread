# Functional Analysis

## Functional purpose
The web app is the primary product interface. It turns the backend Digital Thread into a usable workspace for first-time users, reviewers, and technical users.

## Main actors
- first-time project creator
- engineer or reviewer working on the thread
- manager using dashboard summaries
- documentation reader
- validation user checking a single requirement or goal

## Core flows visible in the UI
- open the dashboard and seed a demo project
- create a project with a domain profile
- enter a project cockpit and follow the recommended workflow
- author requirements, blocks, and test cases
- link objects and inspect traceability through detail views and graph views
- manage evidence, baselines, and change requests
- open authoritative sources and configuration contexts
- run validation cockpit checks
- browse the documentation portal inside the app

## What is complete today
- project dashboard and project list
- profile-aware project cockpit and navigation
- create/edit/detail pages for the main thread objects
- docs portal backed by repository markdown
- progressive disclosure for advanced tabs
- validation cockpit and onboarding wizard
- project import and export entry points

## What is partial or intentionally simplified
- advanced interoperability surfaces are visible but not the same as native standards runtimes
- there is no visible auth or role system in the frontend
- some workflow logic is still driven by route-level composition rather than a dedicated workflow engine

## User-facing rules visible in the UI
- the thread starts with requirements, then realization, then checks
- advanced sections stay available but hidden by default for non-experts
- labels change by domain profile so the vocabulary matches the project type
- empty states are expected to explain what belongs in a section and what to do next

## Practical gaps
- project home and workflow guidance depend on live counts from the API
- the biggest pages still carry a lot of product logic in route files
- the frontend is usable, but many flows depend on the backend being up and reachable
