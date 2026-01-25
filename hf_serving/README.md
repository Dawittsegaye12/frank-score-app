---
title: FrankScore Model API
sdk: docker
app_port: 7860
---

# FrankScore Model API

This Space serves the credit risk models for the FrankScore application.

## Endpoints

- `POST /predict/kenya`: Predicts risk using the Kenya (Financial) Random Forest model.
- `POST /predict/psych`: Predicts risk using the Psychometric XGBoost model.

## Model Artifacts

Models are loaded from the `models/` directory in this repository.
