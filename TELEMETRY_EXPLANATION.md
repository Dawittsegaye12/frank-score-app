# Telemetry System Explanation

## Overview

The `telemetry.js` file implements a comprehensive client-side tracking system that collects **15 metadata features** during the psychometric assessment. These features are used to compute behavior-based trait scores.

---

## Architecture

The system consists of **4 main components**:

1. **TelemetryClient** - Event collection and batching
2. **MetadataTracker** - Aggregates and computes metadata features
3. **IdleTracker** - Detects user inactivity
4. **ScrollTracker** - Tracks scrolling behavior

---

## Component 1: TelemetryClient

### Purpose
Collects events and sends them to the server in batches.

### How It Works

```javascript
class TelemetryClient {
  constructor({ assessmentId, sessionId, endpoint = "/api/events" })
```

**Key Features:**
- **Event Queue**: Stores events in memory before sending
- **Automatic Flushing**: Sends events every 3 seconds (`flushIntervalMs: 3000`)
- **Batch Size**: Sends when queue reaches 30 events (`maxBatch: 30`)
- **Beacon API**: Uses `navigator.sendBeacon()` for reliable delivery on page unload

**Event Structure:**
```javascript
{
  event_name: "question_view",      // Event type
  client_ts_ms: Date.now(),          // Client timestamp
  perf_ts_ms: performance.now(),     // Performance timestamp
  item_id: "1.1",                    // Question ID (if applicable)
  seq: 1,                            // Sequence number
  payload: { ... }                   // Event-specific data
}
```

**Methods:**
- `track(eventName, payload, itemId)` - Add event to queue
- `flush()` - Send queued events to server
- `flushBeacon()` - Send events using Beacon API (for page unload)

---

## Component 2: MetadataTracker

### Purpose
Aggregates raw events into **15 computed metadata features** for behavior-based scoring.

### Initialization

When created, it initializes tracking variables for all 15 features:

```javascript
class MetadataTracker {
  constructor(assessmentId) {
    // Session & Completion
    this.startTime = Date.now();
    this.endTime = null;
    this.completionStatus = 0;
    
    // Response Timing
    this.responseTimes = [];           // Array of response times
    this.questionViewTimes = {};       // item_id -> timestamp
    
    // Click & Hesitation
    this.hesitationTimes = [];        // Time from view to first click
    this.hesitationTimesFinancial = []; // For financial items only
    
    // Answer Behavior
    this.extremeOptions = 0;           // Count of A or D selections
    this.totalAnswers = 0;
    
    // Scroll & Navigation
    this.scrollEvents = 0;
    this.scrollDepths = [];            // Max depth per question
    this.scrollDirections = [];       // +1 down, -1 up
    
    // Reading & Compliance
    this.termsScreenTime = 0;          // Time on terms page
  }
}
```

### Tracking Methods

#### 1. Response Timing

**`recordQuestionView(itemId)`**
- Called when a question is displayed
- Stores timestamp: `questionViewTimes[itemId] = Date.now()`

**`recordAnswerSubmit(itemId)`**
- Called when user submits an answer
- Calculates response time: `(Date.now() - viewTime) / 1000`
- Adds to `responseTimes[]` array

**Example Flow:**
```
User sees question "1.1" → recordQuestionView("1.1")
  → Stores: questionViewTimes["1.1"] = 1234567890

User clicks answer → recordAnswerSubmit("1.1")
  → Calculates: (1234567891 - 1234567890) / 1000 = 1.0 seconds
  → Adds: responseTimes.push(1.0)
```

#### 2. Hesitation Tracking

**`recordFirstInteraction(itemId)`**
- Called on first click/interaction with a question
- Calculates hesitation: time from question view to first click
- Adds to `hesitationTimes[]`
- If financial item (traits 3, 13, 14), also adds to `hesitationTimesFinancial[]`

**Financial Items Detection:**
```javascript
const traitId = parseInt(itemId.split(".")[0], 10);
if ([3, 13, 14].includes(traitId)) {
  this.hesitationTimesFinancial.push(hesitation);
}
```

#### 3. Answer Behavior

**`recordAnswerSelect(itemId, option)`**
- Tracks which option was selected (A, B, C, D)
- Counts extreme options (A or D) for `extremeOptionRate`

**`recordAnswerChange(itemId, fromOption, toOption)`**
- Tracks when user changes their answer
- Increments `answerChanges` counter

#### 4. Scroll Tracking

**`recordScroll(direction, depth)`**
- `direction`: +1 for scrolling down, -1 for scrolling up
- `depth`: Current scroll depth (0-1, where 1 = fully scrolled)
- Increments `scrollEvents` counter
- Stores direction for zigzag calculation

**`saveScrollDepth()`**
- Called when moving to next question
- Saves current max scroll depth to `scrollDepths[]` array
- Resets for next question

#### 5. Completion Tracking

**`markCompleted()`**
- Called when assessment is finished
- Sets `endTime = Date.now()`
- Sets `completionStatus = 1`
- Sets `abandonmentFlag = false`

---

## Component 3: IdleTracker

### Purpose
Detects when user is inactive (no mouse/keyboard/scroll activity).

### How It Works

```javascript
function createIdleTracker(client, metadataTracker, { thresholdMs = 10000 })
```

**Mechanism:**
1. Listens to: `mousemove`, `keydown`, `scroll`, `click`, `touchstart`
2. On any activity: Resets timer
3. If no activity for 10 seconds: Marks as idle
4. Tracks idle periods in `metadataTracker.idlePeriods[]`

**Flow:**
```
User active → Reset timer
  ↓
No activity for 10s → Start idle period
  ↓
User active again → End idle period, record duration
```

---

## Component 4: ScrollTracker

### Purpose
Tracks scrolling behavior per question page.

### How It Works

```javascript
function createScrollTracker(metadataTracker)
```

**Calculations:**
- **Scroll Depth**: `(scrollTop + viewportHeight) / documentHeight`
  - 0 = top of page
  - 1 = bottom of page
- **Zigzag Score**: Counts direction changes (up → down → up)
- **Max Depth**: Highest scroll depth reached per question

**Methods:**
- `reset()` - Called when moving to next question
- `snapshot()` - Returns current scroll statistics

---

## Final Metadata Computation

### `computeMetadata(totalItems = 15)`

This is the **key function** that aggregates all tracked data into the final 15 metadata features.

### Step-by-Step Process

#### 1. Completion Status (Safeguard)
```javascript
// Always set to 1 if assessment is complete
if (hasEndTime || allQuestionsAnswered || hasEnoughResponses) {
  this.completionStatus = 1;
  this.abandonmentFlag = false;
}
```

#### 2. Response Time Statistics
```javascript
// From responseTimes[] array
avg_response_time_sec = average of all response times
median_response_time_sec = median value
min_response_time_sec = minimum value
max_response_time_sec = maximum value
response_time_std_sec = standard deviation
```

#### 3. Hesitation Times
```javascript
hesitation_time_avg = average of hesitationTimes[]
hesitation_time_financial_items = average of hesitationTimesFinancial[]
```

#### 4. Answer Behavior
```javascript
extreme_option_rate = extremeOptions / totalAnswers
// (A or D selections / total selections)
```

#### 5. Scroll Metrics
```javascript
scroll_events_count = total scroll events
scroll_depth_avg = average of scrollDepths[]
scroll_depth_max = maximum of scrollDepths[]
scroll_zigzag_score = direction changes / total scrolls
```

#### 6. Completion Time
```javascript
completion_time_sec = (endTime - startTime) / 1000
```

#### 7. Terms Screen Time
```javascript
terms_screen_time = time spent on terms/consent page
// (Set from sessionStorage by terms page)
```

### Final Output

The function returns a **metadata object** with exactly **15 features**:

```javascript
{
  // Session & Completion (2)
  completion_status: 1,
  completion_time_sec: 65.096,
  
  // Response Timing (6)
  avg_response_time_sec: 4.2096,
  response_time_std_sec: 3.6764,
  median_response_time_sec: 2.647,
  min_response_time_sec: 2.305,
  max_response_time_sec: 16.051,
  
  // Click & Hesitation (2)
  hesitation_time_avg: 2.3403,
  hesitation_time_financial_items: 3.288,
  
  // Answer Behavior (1)
  extreme_option_rate: 0.4667,
  
  // Scroll & Navigation (4)
  scroll_events_count: 167,
  scroll_depth_avg: 0.9081,
  scroll_depth_max: 0.9560,
  scroll_zigzag_score: 0.1807,
  
  // Reading & Compliance (1)
  terms_screen_time: 23.647
}
```

---

## Integration with Questions Page

### Initialization (questions.js)

```javascript
// Create telemetry client
const telemetry = new window.TelemetryClient({ assessmentId, sessionId });

// Create metadata tracker
const metadataTracker = new window.MetadataTracker(assessmentId);

// Create idle tracker (10 second threshold)
const idle = window.createIdleTracker(telemetry, metadataTracker, { thresholdMs: 10000 });

// Create scroll tracker
const scrollTracker = window.createScrollTracker(metadataTracker);
```

### Event Tracking Flow

1. **Question Displayed:**
   ```javascript
   metadataTracker.recordQuestionView(itemId);
   telemetry.track("question_view", {}, itemId);
   ```

2. **User Clicks Option:**
   ```javascript
   metadataTracker.recordFirstInteraction(itemId);  // First click
   metadataTracker.recordAnswerSelect(itemId, option);
   metadataTracker.recordClick();
   ```

3. **User Submits Answer:**
   ```javascript
   metadataTracker.recordAnswerSubmit(itemId);
   telemetry.track("answer_submit", { value: option }, itemId);
   ```

4. **Assessment Complete:**
   ```javascript
   metadataTracker.markCompleted();
   const finalMetadata = metadataTracker.computeMetadata(questions.length);
   telemetry.track("metadata_summary", finalMetadata, null);
   ```

---

## Data Flow Diagram

```
User Interaction
    ↓
Questions Page (questions.js)
    ↓
MetadataTracker (tracks in memory)
    ↓
TelemetryClient (queues events)
    ↓
Automatic Flush (every 3s or 30 events)
    ↓
POST /api/events
    ↓
Server stores in database
    ↓
Assessment Complete
    ↓
computeMetadata() called
    ↓
Final 15 features computed
    ↓
Sent as "metadata_summary" event
    ↓
Server uses for behavior-based trait scoring
```

---

## Key Features

### 1. Real-Time Tracking
- Events tracked as they happen
- No page refresh needed
- Works with single-page application

### 2. Automatic Batching
- Events queued in memory
- Sent in batches (30 events or 3 seconds)
- Reduces server load

### 3. Reliable Delivery
- Uses Beacon API on page unload
- Fallback to fetch with `keepalive: true`
- Ensures data isn't lost

### 4. Privacy-Conscious
- Only tracks interaction patterns
- No personal information collected
- All data stored locally first

### 5. Safeguards
- `completion_status` always set to 1 in `computeMetadata()`
- Handles edge cases (missing data, zero values)
- Validates data before sending

---

## Example: Complete Tracking Flow

**Scenario:** User answers question "1.1"

1. **Question appears:**
   - `recordQuestionView("1.1")` → Stores timestamp

2. **User scrolls:**
   - ScrollTracker detects scroll
   - `recordScroll(+1, 0.5)` → Increments scroll count

3. **User clicks option B:**
   - `recordFirstInteraction("1.1")` → Calculates hesitation (2.3s)
   - `recordAnswerSelect("1.1", "B")` → Not extreme option
   - `recordClick()` → Adds to click timestamps

4. **User clicks "Next":**
   - `recordAnswerSubmit("1.1")` → Calculates response time (4.2s)
   - `saveScrollDepth()` → Saves max scroll depth (0.8)

5. **Events sent:**
   - TelemetryClient batches events
   - Sends to `/api/events` after 3 seconds

6. **Assessment complete:**
   - `markCompleted()` → Sets completion status
   - `computeMetadata(15)` → Computes all 15 features
   - Final metadata sent as `metadata_summary` event

---

## Summary

The telemetry system:
- **Tracks** user interactions in real-time
- **Aggregates** raw events into meaningful metrics
- **Computes** 15 metadata features for behavior scoring
- **Sends** data to server reliably
- **Ensures** data quality with safeguards

All tracking happens **client-side** in the browser, with data sent to the server for storage and analysis.

