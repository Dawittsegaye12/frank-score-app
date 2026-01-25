# FrankScore System Architecture

## Complete System Workflow

```mermaid
graph TB
    Start([User Starts]) --> Login{Login/Signup}
    Login -->|New User| Signup[Signup Page]
    Login -->|Existing User| LoginPage[Login Page]
    
    Signup --> SignupAPI[POST /api/signup]
    LoginPage --> LoginAPI[POST /api/login]
    
    SignupAPI --> CreateUser[Create User in DB]
    LoginAPI --> VerifyUser[Verify Credentials]
    
    CreateUser --> SeedFinancial[Seed Financial Data]
    VerifyUser --> GetFinancial[Get User Financial Data]
    
    SeedFinancial --> Terms[Terms & Consent Page]
    GetFinancial --> Terms
    
    Terms --> StartAPI[POST /api/start]
    StartAPI --> CreateAttempt[Create Assessment Record]
    CreateAttempt --> LinkUser[Link Assessment to User]
    
    LinkUser --> Questions[Questions Page]
    
    Questions --> InitTelemetry[Initialize Telemetry]
    InitTelemetry --> TrackEvents[Track User Interactions]
    
    TrackEvents --> AnswerAPI[POST /api/answer]
    TrackEvents --> EventsAPI[POST /api/events]
    
    AnswerAPI --> StoreAnswer[Store Answer in DB]
    EventsAPI --> StoreEvents[Store Events in DB]
    
    Questions --> Complete[All Questions Answered]
    Complete --> CompleteAPI[POST /api/complete]
    
    CompleteAPI --> GetData[Retrieve Answers & Events]
    GetData --> ComputeMetadata[Compute 15 Metadata Features]
    GetData --> ComputeTraits[Compute Traits]
    
    ComputeMetadata --> BehaviorTraits[Behavior-Based Traits]
    ComputeTraits --> ContentTraits[Content-Based Traits]
    
    ContentTraits --> CombinedTraits[Combined Traits<br/>60% Behavior + 40% Content]
    BehaviorTraits --> CombinedTraits
    
    CombinedTraits --> PsychPD[Psychometric PD<br/>XGBoost Model]
    
    CompleteAPI --> GetUserFinancial[Get User Financial Data]
    GetUserFinancial --> FinancialPD{Financial PD}
    
    FinancialPD -->|Model Available| RFModel[Random Forest Model<br/>23 Features]
    FinancialPD -->|Model Failed| FallbackPD[Fallback Heuristic]
    
    RFModel --> FinPD[Financial PD Value]
    FallbackPD --> FinPD
    
    PsychPD --> CombinedPD[Combined PD<br/>60% Financial + 40% Psychometric]
    FinPD --> CombinedPD
    
    CombinedPD --> StoreResults[Store Results in DB]
    StoreResults --> Results[Results Page]
    
    Results --> Display[Display PD Values & Traits]
    
    style Start fill:#e1f5ff
    style Login fill:#fff4e6
    style Questions fill:#e8f5e9
    style CompleteAPI fill:#f3e5f5
    style PsychPD fill:#fff3e0
    style RFModel fill:#fff3e0
    style Results fill:#e1f5ff
```

## Component Architecture

```mermaid
graph LR
    subgraph "Frontend (Browser)"
        A[Login/Signup Pages] --> B[Terms Page]
        B --> C[Questions Page]
        C --> D[Results Page]
        
        C --> E[TelemetryClient]
        C --> F[MetadataTracker]
        C --> G[IdleTracker]
        C --> H[ScrollTracker]
        
        E --> I[Event Queue]
        F --> J[Metadata Aggregation]
    end
    
    subgraph "Backend (FastAPI)"
        K[Authentication Endpoints] --> L[Assessment Endpoints]
        L --> M[Scoring Engine]
        
        K --> N[User Management]
        L --> O[Event Storage]
        M --> P[Trait Computation]
        M --> Q[PD Calculation]
    end
    
    subgraph "Database (SQLite)"
        R[(Users Table)] --> S[(Financial Data Table)]
        T[(Attempts Table)] --> U[(Responses Table)]
        T --> V[(Events Table)]
        T --> W[(Computed Table)]
    end
    
    subgraph "Models"
        X[XGBoost Model<br/>Psychometric PD] --> Q
        Y[Random Forest Model<br/>Financial PD] --> Q
    end
    
    A --> K
    C --> L
    E --> L
    F --> L
    M --> R
    M --> S
    M --> T
    M --> U
    M --> V
    M --> W
    P --> X
    Q --> Y
    
    style A fill:#e3f2fd
    style C fill:#e8f5e9
    style M fill:#fff3e0
    style X fill:#fce4ec
    style Y fill:#fce4ec
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI Backend
    participant DB as SQLite Database
    participant M as ML Models
    
    U->>F: Login (username/password)
    F->>API: POST /api/login
    API->>DB: Verify user credentials
    DB-->>API: User data + Financial data
    API-->>F: user_id + username
    F->>F: Store in sessionStorage
    
    U->>F: Accept Terms
    F->>API: POST /api/start (with user_id)
    API->>DB: Create assessment record
    DB-->>API: assessment_id + session_id
    API-->>F: assessment_id + session_id
    
    U->>F: Answer Questions
    F->>F: Track interactions (Telemetry)
    F->>API: POST /api/answer
    F->>API: POST /api/events (batched)
    API->>DB: Store answers
    API->>DB: Store events
    
    U->>F: Complete Assessment
    F->>API: POST /api/complete
    API->>DB: Get all answers & events
    DB-->>API: Answers + Events
    
    API->>API: Compute 15 Metadata Features
    API->>API: Compute Content Traits (from answers)
    API->>API: Compute Behavior Traits (from metadata)
    API->>API: Combine Traits (60% behavior + 40% content)
    
    API->>M: Predict Psychometric PD (XGBoost)
    M-->>API: pd_psych_hat
    
    API->>DB: Get user financial data
    DB-->>API: Financial features (23 fields)
    API->>M: Predict Financial PD (Random Forest)
    M-->>API: pd_fin_hat (or fallback)
    
    API->>API: Combine PDs (60% financial + 40% psychometric)
    API->>DB: Store computed results
    DB-->>API: Success
    
    API-->>F: Results ready
    F->>API: GET /api/result
    API->>DB: Get computed results
    DB-->>API: Traits + PDs
    API-->>F: JSON response
    F->>U: Display Results
```

## Database Schema

```mermaid
erDiagram
    USERS ||--o{ ATTEMPTS : "has"
    USERS ||--|| FINANCIAL_DATA : "has"
    ATTEMPTS ||--o{ RESPONSES : "contains"
    ATTEMPTS ||--o{ EVENTS : "contains"
    ATTEMPTS ||--o| COMPUTED : "produces"
    
    USERS {
        int id PK
        string username UK
        string password_hash
        string email
        int created_at_ms
        int last_login_ms
    }
    
    FINANCIAL_DATA {
        int user_id PK,FK
        string customer_id
        float num_previous_loans
        float Total_Amount
        float daily_burden
        float burden_ratio
        float borrower_history_strength
        ... 23 features total
    }
    
    ATTEMPTS {
        string assessment_id PK
        int user_id FK
        string session_id
        string status
        int started_at_ms
        int completed_at_ms
    }
    
    RESPONSES {
        int id PK
        string assessment_id FK
        string item_id
        string selected_option
        int answered_at_ms
    }
    
    EVENTS {
        int id PK
        string assessment_id FK
        string session_id
        string event_name
        int client_ts_ms
        float perf_ts_ms
        string item_id
        int seq
        string payload_json
    }
    
    COMPUTED {
        int id PK
        string assessment_id FK,UK
        string metadata_json
        string traits_json
        float pd_psych_hat
        float pd_fin_hat
        float pd_final_hat
    }
```

## Scoring Pipeline

```mermaid
graph TD
    Start([Assessment Complete]) --> GetData[Get Answers & Events from DB]
    
    GetData --> Answers[Answers by Item<br/>item_id → selected_option]
    GetData --> Events[Raw Events Array]
    
    Answers --> ContentScoring[Content-Based Scoring]
    Events --> MetadataComputation[Metadata Computation]
    
    ContentScoring --> ScoreMap[Lookup Score Map<br/>A/B/C/D → 0-3]
    ScoreMap --> TraitScores[Average Scores per Trait]
    TraitScores --> NormalizeContent[Normalize to 0-1]
    
    MetadataComputation --> MetadataFeatures[15 Metadata Features]
    MetadataFeatures --> BehaviorScoring[Behavior-Based Scoring]
    BehaviorScoring --> NormalizeBehavior[Normalize to 0-1]
    
    NormalizeContent --> Combine[Combine Traits<br/>α = 0.6]
    NormalizeBehavior --> Combine
    
    Combine --> FinalTraits[15 Final Traits]
    
    FinalTraits --> XGBModel[XGBoost Model]
    XGBModel --> PsychPD[Psychometric PD]
    
    Start --> GetFinancial[Get User Financial Data]
    GetFinancial --> RFModel{Random Forest Model}
    
    RFModel -->|Success| ModelPD[Model Prediction]
    RFModel -->|Failed| HeuristicPD[Fallback Heuristic]
    
    ModelPD --> FinancialPD[Financial PD]
    HeuristicPD --> FinancialPD
    
    PsychPD --> CombinePD[Combine PDs<br/>60% Financial + 40% Psychometric]
    FinancialPD --> CombinePD
    
    CombinePD --> FinalPD[Final PD]
    
    FinalTraits --> Store[Store in Database]
    PsychPD --> Store
    FinancialPD --> Store
    FinalPD --> Store
    
    Store --> Done([Results Available])
    
    style Start fill:#e1f5ff
    style FinalTraits fill:#e8f5e9
    style PsychPD fill:#fff3e0
    style FinancialPD fill:#fff3e0
    style FinalPD fill:#f3e5f5
    style Done fill:#e1f5ff
```

## Telemetry Tracking Flow

```mermaid
graph LR
    subgraph "User Interactions"
        A[Question View] --> B[Scroll]
        B --> C[Click Option]
        C --> D[Submit Answer]
        D --> E[Next Question]
    end
    
    subgraph "Tracking Components"
        A --> F[MetadataTracker.recordQuestionView]
        B --> G[ScrollTracker.recordScroll]
        C --> H[MetadataTracker.recordFirstInteraction]
        C --> I[MetadataTracker.recordAnswerSelect]
        D --> J[MetadataTracker.recordAnswerSubmit]
    end
    
    subgraph "Event Collection"
        F --> K[TelemetryClient.track]
        G --> K
        H --> K
        I --> K
        J --> K
    end
    
    subgraph "Batching & Sending"
        K --> L[Event Queue]
        L --> M{Queue Size >= 30<br/>OR<br/>3 seconds elapsed?}
        M -->|Yes| N[POST /api/events]
        M -->|No| L
    end
    
    subgraph "Server Storage"
        N --> O[Store in Events Table]
    end
    
    subgraph "Final Computation"
        E --> P[Assessment Complete]
        P --> Q[computeMetadata]
        Q --> R[15 Metadata Features]
        R --> S[POST /api/events<br/>metadata_summary]
        S --> O
    end
    
    style A fill:#e3f2fd
    style K fill:#fff3e0
    style Q fill:#e8f5e9
    style R fill:#f3e5f5
```

## Authentication & Authorization Flow

```mermaid
stateDiagram-v2
    [*] --> NotAuthenticated
    
    NotAuthenticated --> LoginPage: Navigate to /
    NotAuthenticated --> SignupPage: Click Sign Up
    
    LoginPage --> Authenticating: Submit Credentials
    SignupPage --> CreatingAccount: Submit Form
    
    CreatingAccount --> AccountCreated: User Created
    AccountCreated --> Authenticated: Auto-login
    
    Authenticating --> Authenticated: Valid Credentials
    Authenticating --> LoginPage: Invalid Credentials
    
    Authenticated --> TermsPage: Agree to Terms
    TermsPage --> AssessmentStarted: Start Assessment
    
    AssessmentStarted --> QuestionsPage: Begin Questions
    QuestionsPage --> AssessmentComplete: All Answered
    
    AssessmentComplete --> ResultsPage: View Results
    ResultsPage --> [*]
    
    Authenticated --> Logout: User Logs Out
    Logout --> NotAuthenticated
```

## Model Integration Flow

```mermaid
graph TD
    Start([Server Startup]) --> LoadXGB[Load XGBoost Model]
    Start --> LoadRF[Load Random Forest Model]
    
    LoadXGB --> XGBReady{XGB Model<br/>Available?}
    LoadRF --> RFReady{RF Model<br/>Available?}
    
    XGBReady -->|Yes| XGBLoaded[Model Loaded<br/>Feature Columns: 15 traits]
    XGBReady -->|No| XGBFallback[Use Fallback Scoring]
    
    RFReady -->|Yes| RFLoaded[Model Loaded<br/>Feature Columns: 23 financial]
    RFReady -->|No| RFFallback[Use Fallback Heuristic]
    
    Assessment([Assessment Complete]) --> GetTraits[Get Computed Traits]
    Assessment --> GetFinancial[Get Financial Data]
    
    GetTraits --> XGBPredict[Predict Psychometric PD]
    GetFinancial --> RFPredict[Predict Financial PD]
    
    XGBPredict --> XGBLoaded
    XGBPredict --> XGBFallback
    XGBLoaded --> PsychPD[Psychometric PD Value]
    XGBFallback --> PsychPD
    
    RFPredict --> RFLoaded
    RFPredict --> RFFallback
    RFLoaded --> FinPD[Financial PD Value]
    RFFallback --> FinPD
    
    PsychPD --> Combine[Combine PDs]
    FinPD --> Combine
    
    Combine --> FinalPD[Final PD = 0.6 × Fin + 0.4 × Psych]
    
    style Start fill:#e1f5ff
    style XGBLoaded fill:#fff3e0
    style RFLoaded fill:#fff3e0
    style PsychPD fill:#e8f5e9
    style FinPD fill:#e8f5e9
    style FinalPD fill:#f3e5f5
```

## Complete System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        LoginUI[Login/Signup UI]
        QuestionsUI[Questions UI]
        ResultsUI[Results UI]
    end
    
    subgraph "Frontend Logic"
        Telemetry[Telemetry System]
        Metadata[Metadata Tracker]
        QuestionsJS[Questions Handler]
    end
    
    subgraph "API Layer"
        AuthAPI[Authentication API]
        AssessmentAPI[Assessment API]
        ScoringAPI[Scoring API]
    end
    
    subgraph "Business Logic"
        Scoring[Scoring Engine]
        TraitCompute[Trait Computation]
        PDCompute[PD Computation]
    end
    
    subgraph "Data Layer"
        UserDB[(Users)]
        FinancialDB[(Financial Data)]
        AssessmentDB[(Assessments)]
        EventsDB[(Events)]
        ResultsDB[(Results)]
    end
    
    subgraph "ML Models"
        XGBModel[XGBoost<br/>Psychometric PD]
        RFModel[Random Forest<br/>Financial PD]
    end
    
    Browser --> LoginUI
    Browser --> QuestionsUI
    Browser --> ResultsUI
    
    LoginUI --> AuthAPI
    QuestionsUI --> AssessmentAPI
    QuestionsUI --> Telemetry
    ResultsUI --> AssessmentAPI
    
    Telemetry --> Metadata
    Metadata --> AssessmentAPI
    QuestionsJS --> AssessmentAPI
    
    AuthAPI --> UserDB
    AssessmentAPI --> AssessmentDB
    AssessmentAPI --> EventsDB
    AssessmentAPI --> ScoringAPI
    
    ScoringAPI --> Scoring
    Scoring --> TraitCompute
    Scoring --> PDCompute
    
    TraitCompute --> XGBModel
    PDCompute --> RFModel
    
    ScoringAPI --> UserDB
    ScoringAPI --> FinancialDB
    ScoringAPI --> ResultsDB
    
    XGBModel --> PDCompute
    RFModel --> PDCompute
    
    PDCompute --> ResultsDB
    ResultsDB --> ResultsUI
    
    style Browser fill:#e3f2fd
    style Scoring fill:#fff3e0
    style XGBModel fill:#fce4ec
    style RFModel fill:#fce4ec
    style ResultsDB fill:#e8f5e9
```

