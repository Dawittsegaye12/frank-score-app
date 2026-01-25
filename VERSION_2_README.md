# FrankScore Version 2 - User Authentication & Model Integration

## Overview

Version 2 of the FrankScore application introduces:
1. **User Authentication**: Login and signup functionality
2. **Persona System**: Pre-populated financial profiles for testing
3. **Random Forest Model Integration**: Uses trained model for financial PD prediction
4. **Streamlined Flow**: Login → Terms → Psychometric Assessment → Results

## Key Changes

### Database Schema

**New Tables:**
- `users`: Stores user accounts (username, password_hash, email)
- `financial_data`: Stores persona financial data matching CSV features
- `attempts`: Now includes `user_id` to link assessments to users

### Authentication

**Endpoints:**
- `GET /login` - Login page
- `GET /signup` - Signup page
- `POST /api/login` - Login API
- `POST /api/signup` - Signup API

**Credentials:**
All seeded personas use password: `password123`

### Persona System

The application includes 11 pre-seeded personas with different risk profiles:

**Low Risk (3 personas):**
- `alice`, `bob`, `charlie`

**Medium Risk (3 personas):**
- `diana`, `eve`, `frank`

**High Risk (3 personas):**
- `grace`, `henry`, `ivy`

**New Users (2 personas):**
- `john`, `jane`

### Financial PD Prediction

**Model Integration:**
- Uses `models/random_forest.joblib` for financial PD prediction
- Model expects features from `kenya_engineered_features_borrower_side.csv`
- Features are automatically extracted from user's `financial_data` record
- Falls back to deterministic calculation if model unavailable

**Flow:**
1. User logs in
2. User agrees to terms (consents to use financial data)
3. Assessment starts with user's financial profile
4. After psychometric assessment, financial PD is computed using:
   - User's persona financial data → Random Forest model → PD prediction
5. Combined PD = 60% financial + 40% psychometric

### Application Flow

**Version 2 Flow:**
```
Login/Signup → Terms (with consent) → Psychometric Questions → Results
```

**Removed:**
- Financial form page (no longer needed - uses persona data)

## Setup Instructions

### Quick Start (Recommended)

Use the provided startup scripts to automatically set up and run everything:

**On Linux/Mac/Git Bash:**
```bash
./run.sh
```

**On Windows (PowerShell):**
```powershell
.\run.ps1
```

**On Windows (Command Prompt):**
```cmd
run.bat
```

The scripts will automatically:
1. Check Python installation
2. Create and activate virtual environment
3. Install dependencies
4. Initialize database
5. Seed personas (if needed)
6. Start the server

### Manual Setup

If you prefer manual setup:

#### 1. Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `.venv\Scripts\activate.bat`
- **Linux/Mac:** `source .venv/bin/activate`

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Seed Personas

Run the seeding script to create test users:

```bash
python seed_personas.py
```

This creates 11 personas with financial profiles matching the model's expected features.

#### 4. Start the Server

```bash
uvicorn app:app --reload --port 8000
```

### 3. Access the Application

1. Navigate to `http://localhost:8000`
2. You'll be redirected to the login page
3. Login with any seeded persona (e.g., `alice` / `password123`)
4. Agree to terms
5. Complete the psychometric assessment
6. View results with financial PD from the Random Forest model

## Technical Details

### Model Features

The Random Forest model expects these features (from CSV):
- `num_previous_loans`
- `avg_time_bw_loans`
- `avg_past_amount`
- `avg_past_daily_burden`
- `std_past_amount`
- `std_past_daily_burden`
- `trend_in_amount`
- `trend_in_burden`
- `Total_Amount`
- `daily_burden`
- `amount_ratio`
- `burden_ratio`
- `amount_bucket`
- `burden_percentile`
- `borrower_history_strength`
- `month`, `quarter`, `week_of_year`
- `days_to_salary_day`
- `days_to_local_festival`
- `account_age_days`
- `loan_frequency_per_year`
- `latest_amount_ma3`

### Code Changes

**Files Modified:**
- `app.py`: Added authentication endpoints, updated flow
- `db.py`: Added users and financial_data tables/functions
- `scoring.py`: Added Random Forest model integration
- `templates/terms.html`: Updated to reflect new flow
- `static/questions.js`: Removed financial page navigation

**Files Created:**
- `seed_personas.py`: Persona seeding script
- `templates/login.html`: Login page
- `templates/signup.html`: Signup page

## Testing

### Test Different Risk Profiles

1. **Low Risk User:**
   - Login: `alice` / `password123`
   - Expected: Lower financial PD

2. **High Risk User:**
   - Login: `grace` / `password123`
   - Expected: Higher financial PD

3. **New User:**
   - Login: `john` / `password123`
   - Expected: Default/moderate PD (no history)

### Verify Model Integration

Check server logs on startup:
```
Info: Random Forest model loaded with 23 feature columns
```

Check results page - `pd_fin_hat` should be computed from the model.

## Migration Notes

**From Version 1:**
- Old assessments without `user_id` will still work
- Financial PD will fall back to deterministic calculation if no user data
- New assessments require login

## Future Enhancements

- Session management (JWT tokens)
- Password reset functionality
- User dashboard to view assessment history
- Admin panel to manage personas
- Real-time model retraining

