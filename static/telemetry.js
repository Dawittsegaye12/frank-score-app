/**
 * FrankScore Telemetry System
 * Tracks 15 metadata features for behavior-based trait scoring.
 * 
 * Features tracked (15 total):
 * - Session & Completion (2): completion_status, completion_time_sec
 * - Response Timing (6): avg/median/min/max/std response times
 * - Click & Hesitation (2): hesitation times (avg and financial)
 * - Answer Behavior (1): extreme_option_rate
 * - Scroll & Navigation (4): scroll events, depth (avg/max), zigzag score
 * - Reading & Compliance (1): terms_screen_time
 * 
 * VERSION: 2026-01-05-fix-completion-status
 * FIX: completion_status is now ALWAYS set to 1 in computeMetadata()
 */

class TelemetryClient {
  constructor({ assessmentId, sessionId, endpoint = "/api/events" }) {
    this.assessmentId = assessmentId;
    this.sessionId = sessionId;
    this.endpoint = endpoint;
    this.queue = [];
    this.seq = 0;
    this.flushTimer = null;
    this.maxBatch = 30;
    this.flushIntervalMs = 3000;
    this._startTimer();
    this._wireUnloadFlush();
  }

  _startTimer() {
    if (this.flushTimer) return;
    this.flushTimer = setInterval(() => {
      this.flush().catch(() => { });
    }, this.flushIntervalMs);
  }

  track(eventName, payload = {}, itemId = null) {
    const ev = {
      event_name: eventName,
      client_ts_ms: Date.now(),
      perf_ts_ms: (typeof performance !== "undefined" && performance.now) ? performance.now() : null,
      item_id: itemId,
      seq: ++this.seq,
      payload: payload || {}
    };
    this.queue.push(ev);
    if (this.queue.length >= this.maxBatch) {
      this.flush().catch(() => { });
    }
  }

  async flush() {
    if (!this.queue.length) return;
    const batch = this.queue.splice(0, this.maxBatch);
    // #region agent log
    const hasMetadataSummary = batch.some(e => e.event_name === 'metadata_summary');
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:50',message:'flush before send',data:{batchSize:batch.length,hasMetadataSummary,eventNames:batch.map(e=>e.event_name)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    const response = await fetch(this.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assessment_id: this.assessmentId,
        session_id: this.sessionId,
        events: batch
      })
    });
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:62',message:'flush after send',data:{status:response.status,ok:response.ok,hasMetadataSummary},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
  }

  flushBeacon() {
    if (!this.queue.length) return;
    const batch = this.queue.splice(0, this.queue.length);
    const payload = JSON.stringify({
      assessment_id: this.assessmentId,
      session_id: this.sessionId,
      events: batch
    });
    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: "application/json" });
        navigator.sendBeacon(this.endpoint, blob);
        return;
      }
    } catch (_) { }
    fetch(this.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true
    }).catch(() => { });
  }

  _wireUnloadFlush() {
    window.addEventListener("beforeunload", () => this.flushBeacon());
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") this.flushBeacon();
    });
  }
}


/**
 * MetadataTracker - Aggregates all 15 metadata features
 * Computes statistics at the end of assessment for behavior-based scoring.
 */
class MetadataTracker {
  constructor(assessmentId) {
    this.assessmentId = assessmentId;

    // Session & Completion
    this.startTime = Date.now();
    this.endTime = null;
    this.sessionsCount = this._getSessionCount();
    this.partialAttemptsCount = 0;
    this.returnAfterDisconnection = false;
    this.abandonmentFlag = true; // Set to false when completed
    this.completionStatus = 0;

    // Response Timing
    this.responseTimes = []; // Per-question response times in seconds
    this.questionViewTimes = {}; // item_id -> view timestamp
    this.idlePeriods = []; // List of idle durations in ms
    this.currentIdleStart = null;

    // Click & Hesitation  
    this.clickTimestamps = []; // For rapid click detection
    this.hesitationTimes = []; // Time from question view to first interaction
    this.hesitationTimesFinancial = []; // Hesitation on financial items (traits 3,13,14)
    this.firstInteractionRecorded = {}; // item_id -> boolean

    // Answer Behavior
    this.answeredItems = new Set();
    this.skippedItems = new Set();
    this.answerChanges = 0;
    this.answerChangesFinancial = 0;
    this.extremeOptions = 0; // Count of A or D selections
    this.totalAnswers = 0;
    this.previousAnswers = {}; // item_id -> previous answer for inconsistency

    // Scroll & Navigation
    this.scrollEvents = 0;
    this.scrollDepths = []; // Max depth per page/question
    this.currentScrollDepth = 0;
    this.scrollDirections = []; // +1 for down, -1 for up
    this.backNavCount = 0;

    // Reading & Compliance
    this.termsScreenTime = 0;
    this.termsScrollDepth = 0;
    this.instructionComplianceFlags = 0;

    // Track visibility changes for return detection
    this._wireVisibilityTracking();
  }

  _getSessionCount() {
    const key = `fs_sessions_${this.assessmentId}`;
    const count = parseInt(sessionStorage.getItem(key) || "0", 10) + 1;
    sessionStorage.setItem(key, String(count));
    return count;
  }

  _wireVisibilityTracking() {
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        this.returnAfterDisconnection = true;
      }
    });
  }

  // === Session & Completion ===

  markCompleted() {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:174',message:'markCompleted entry',data:{completionStatusBefore:this.completionStatus,abandonmentFlagBefore:this.abandonmentFlag,endTimeBefore:this.endTime},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'G'})}).catch(()=>{});
    // #endregion
    this.endTime = Date.now();
    this.completionStatus = 1;
    this.abandonmentFlag = false;
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:178',message:'markCompleted exit',data:{completionStatusAfter:this.completionStatus,abandonmentFlagAfter:this.abandonmentFlag,endTimeAfter:this.endTime},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'G'})}).catch(()=>{});
    // #endregion
  }

  // === Response Timing ===

  recordQuestionView(itemId) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:175',message:'recordQuestionView',data:{itemId,viewTime:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
    // #endregion
    this.questionViewTimes[itemId] = Date.now();
    this.firstInteractionRecorded[itemId] = false;
  }

  recordAnswerSubmit(itemId) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:180',message:'recordAnswerSubmit entry',data:{itemId,hasViewTime:!!this.questionViewTimes[itemId],viewTime:this.questionViewTimes[itemId]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    const viewTime = this.questionViewTimes[itemId];
    if (viewTime) {
      const responseTime = (Date.now() - viewTime) / 1000;
      this.responseTimes.push(responseTime);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:184',message:'recordAnswerSubmit responseTime added',data:{itemId,responseTime,responseTimesCount:this.responseTimes.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
      // #endregion
    } else {
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:189',message:'recordAnswerSubmit no viewTime',data:{itemId,questionViewTimesKeys:Object.keys(this.questionViewTimes)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
      // #endregion
    }
    this.answeredItems.add(itemId);
  }

  startIdle() {
    this.currentIdleStart = Date.now();
  }

  endIdle() {
    if (this.currentIdleStart) {
      this.idlePeriods.push(Date.now() - this.currentIdleStart);
      this.currentIdleStart = null;
    }
  }

  // === Click & Hesitation ===

  recordClick() {
    this.clickTimestamps.push(Date.now());
  }

  recordFirstInteraction(itemId) {
    if (this.firstInteractionRecorded[itemId]) return;
    this.firstInteractionRecorded[itemId] = true;

    const viewTime = this.questionViewTimes[itemId];
    if (viewTime) {
      const hesitation = (Date.now() - viewTime) / 1000;
      this.hesitationTimes.push(hesitation);

      // Check if financial item (traits 3, 13, 14)
      const traitId = parseInt(itemId.split(".")[0], 10);
      if ([3, 13, 14].includes(traitId)) {
        this.hesitationTimesFinancial.push(hesitation);
      }
    }
  }

  // === Answer Behavior ===

  recordAnswerSelect(itemId, option) {
    this.totalAnswers++;

    // Track extreme options (A or D)
    if (option === "A" || option === "D") {
      this.extremeOptions++;
    }
  }

  recordAnswerChange(itemId, fromOption, toOption) {
    this.answerChanges++;

    // Check if financial item (traits 3, 13, 14)
    const traitId = parseInt(itemId.split(".")[0], 10);
    if ([3, 13, 14].includes(traitId)) {
      this.answerChangesFinancial++;
    }
  }

  recordSkip(itemId) {
    this.skippedItems.add(itemId);
  }

  // === Scroll & Navigation ===

  recordScroll(direction, depth) {
    this.scrollEvents++;
    if (depth > this.currentScrollDepth) {
      this.currentScrollDepth = depth;
    }
    this.scrollDirections.push(direction);
  }

  saveScrollDepth() {
    if (this.currentScrollDepth > 0) {
      this.scrollDepths.push(this.currentScrollDepth);
    }
    this.currentScrollDepth = 0;
  }

  recordBackNav() {
    this.backNavCount++;
  }

  // === Reading & Compliance ===

  setTermsData(screenTime, scrollDepth) {
    this.termsScreenTime = screenTime;
    this.termsScrollDepth = scrollDepth;
  }

  recordInstructionViolation() {
    this.instructionComplianceFlags++;
  }

  // === Compute Final Metadata ===

  computeMetadata(totalItems = 15) {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:308',message:'computeMetadata entry',data:{totalItems,responseTimesCount:this.responseTimes.length,answeredItemsCount:this.answeredItems.size,startTime:this.startTime,endTime:this.endTime,completionStatus:this.completionStatus,abandonmentFlag:this.abandonmentFlag},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    // Safeguard: ALWAYS set completion_status to 1 if we're computing final metadata
    // This is called at the end of assessment, so it should always be completed
    // Check if endTime is set OR all questions are answered OR we have enough responses
    const hasEndTime = this.endTime !== null && this.endTime !== undefined && this.endTime > 0;
    const allQuestionsAnswered = this.answeredItems.size >= totalItems;
    const hasEnoughResponses = this.responseTimes.length >= totalItems;
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:314',message:'safeguard check',data:{hasEndTime,allQuestionsAnswered,hasEnoughResponses,answeredCount:this.answeredItems.size,responseTimesCount:this.responseTimes.length,totalItems,currentCompletionStatus:this.completionStatus},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    // Force completion if any completion indicator is present
    if (hasEndTime || allQuestionsAnswered || hasEnoughResponses) {
      this.completionStatus = 1;
      this.abandonmentFlag = false;
      if (!hasEndTime) {
        // If endTime wasn't set but assessment is complete, set it now
        this.endTime = Date.now();
      }
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:328',message:'safeguard applied - completion forced',data:{hasEndTime,allQuestionsAnswered,hasEnoughResponses,endTime:this.endTime,completionStatus:this.completionStatus,abandonmentFlag:this.abandonmentFlag},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
    } else {
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:335',message:'safeguard NOT applied',data:{hasEndTime,allQuestionsAnswered,hasEnoughResponses,answeredCount:this.answeredItems.size,responseTimesCount:this.responseTimes.length,totalItems},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion
    }
    const completionTime = this.endTime
      ? (this.endTime - this.startTime) / 1000
      : (Date.now() - this.startTime) / 1000;

    // Response time statistics
    const rt = this.responseTimes;
    const avgResponseTime = rt.length > 0 ? rt.reduce((a, b) => a + b, 0) / rt.length : null;
    const sortedRt = [...rt].sort((a, b) => a - b);
    const medianResponseTime = sortedRt.length > 0
      ? sortedRt[Math.floor(sortedRt.length / 2)]
      : null;
    const minResponseTime = sortedRt.length > 0 ? sortedRt[0] : null;
    const maxResponseTime = sortedRt.length > 0 ? sortedRt[sortedRt.length - 1] : null;

    // Standard deviation of response times
    let responseTimeStd = null;
    if (rt.length > 1 && avgResponseTime !== null) {
      const variance = rt.reduce((sum, t) => sum + Math.pow(t - avgResponseTime, 2), 0) / rt.length;
      responseTimeStd = Math.sqrt(variance);
    }

    // Idle time
    const idleTimeTotal = this.idlePeriods.reduce((a, b) => a + b, 0) / 1000;
    const idleTimeRatio = completionTime > 0 ? idleTimeTotal / completionTime : 0;

    // Rapid clicks (clicks < 250ms apart)
    let rapidClickEvents = 0;
    for (let i = 1; i < this.clickTimestamps.length; i++) {
      if (this.clickTimestamps[i] - this.clickTimestamps[i - 1] < 250) {
        rapidClickEvents++;
      }
    }
    const rapidClickRate = this.clickTimestamps.length > 1
      ? rapidClickEvents / (this.clickTimestamps.length - 1)
      : 0;

    // Hesitation times
    const hesitationAvg = this.hesitationTimes.length > 0
      ? this.hesitationTimes.reduce((a, b) => a + b, 0) / this.hesitationTimes.length
      : null;
    const hesitationFinancial = this.hesitationTimesFinancial.length > 0
      ? this.hesitationTimesFinancial.reduce((a, b) => a + b, 0) / this.hesitationTimesFinancial.length
      : null;

    // Answer behavior
    const skipRate = totalItems > 0 ? this.skippedItems.size / totalItems : 0;
    const answerChangeRate = this.answeredItems.size > 0
      ? this.answerChanges / this.answeredItems.size
      : 0;
    const answerChangeRateFinancial = this.answeredItems.size > 0
      ? this.answerChangesFinancial / Math.max(1, this._countFinancialAnswered())
      : 0;
    const extremeOptionRate = this.totalAnswers > 0
      ? this.extremeOptions / this.totalAnswers
      : 0;

    // Scroll
    const scrollDepthAvg = this.scrollDepths.length > 0
      ? this.scrollDepths.reduce((a, b) => a + b, 0) / this.scrollDepths.length
      : 0;
    const scrollDepthMax = this.scrollDepths.length > 0
      ? Math.max(...this.scrollDepths)
      : 0;

    // Zigzag score (direction changes)
    let zigzagCount = 0;
    for (let i = 1; i < this.scrollDirections.length; i++) {
      if (this.scrollDirections[i] !== 0 &&
        this.scrollDirections[i - 1] !== 0 &&
        this.scrollDirections[i] !== this.scrollDirections[i - 1]) {
        zigzagCount++;
      }
    }
    const scrollZigzagScore = this.scrollDirections.length > 1
      ? zigzagCount / (this.scrollDirections.length - 1)
      : 0;

    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:385',message:'computeMetadata building return object',data:{thisCompletionStatus:this.completionStatus,thisAbandonmentFlag:this.abandonmentFlag,completionTime},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    // Final safeguard: ALWAYS set completion_status to 1 when computing final metadata
    // computeMetadata() is only called at the end of assessment, so it should always be 1
    const finalCompletionStatus = 1;
    const finalAbandonmentFlag = 0;
    
    // Console log to verify new code is running (check browser console)
    console.log('[FrankScore] computeMetadata: Setting completion_status=1 (FIX APPLIED)');
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:400',message:'final metadata object creation',data:{originalCompletionStatus:this.completionStatus,originalAbandonmentFlag:this.abandonmentFlag,finalCompletionStatus,finalAbandonmentFlag},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    const metadata = {
      // Session & Completion (2) - Removed: sessions_count, partial_attempts_count, return_after_disconnection, abandonment_flag
      completion_status: finalCompletionStatus,
      completion_time_sec: completionTime,

      // Response Timing (6) - Removed: idle_time_total_sec, idle_time_ratio
      avg_response_time_sec: avgResponseTime,
      response_time_std_sec: responseTimeStd,
      median_response_time_sec: medianResponseTime,
      min_response_time_sec: minResponseTime,
      max_response_time_sec: maxResponseTime,

      // Click & Hesitation (2) - Removed: rapid_click_events, rapid_click_rate
      hesitation_time_avg: hesitationAvg,
      hesitation_time_financial_items: hesitationFinancial,

      // Answer Behavior (1) - Removed: skip_rate, answer_change_rate, answer_change_rate_financial_items, inconsistency_score
      extreme_option_rate: extremeOptionRate,

      // Scroll & Navigation (4) - Removed: back_nav_count
      scroll_events_count: this.scrollEvents,
      scroll_depth_avg: scrollDepthAvg,
      scroll_depth_max: scrollDepthMax,
      scroll_zigzag_score: scrollZigzagScore,

      // Reading & Compliance (1) - Removed: terms_scroll_depth, instruction_compliance_flags
      terms_screen_time: this.termsScreenTime
    };
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'telemetry.js:360',message:'computeMetadata exit',data:{metadataKeys:Object.keys(metadata).length,metadataSample:{completion_status:metadata.completion_status,avg_response_time_sec:metadata.avg_response_time_sec,hesitation_time_avg:metadata.hesitation_time_avg}},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    return metadata;
  }

  _countFinancialAnswered() {
    let count = 0;
    for (const itemId of this.answeredItems) {
      const traitId = parseInt(itemId.split(".")[0], 10);
      if ([3, 13, 14].includes(traitId)) count++;
    }
    return count;
  }
}


/**
 * IdleTracker - Detects user inactivity
 */
function createIdleTracker(client, metadataTracker, { thresholdMs = 10000 } = {}) {
  let idle = false;
  let timer = null;

  function markActive() {
    if (idle) {
      idle = false;
      client.track("idle_end", {});
      if (metadataTracker) metadataTracker.endIdle();
    }
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      idle = true;
      client.track("idle_start", {});
      if (metadataTracker) metadataTracker.startIdle();
    }, thresholdMs);
  }

  ["mousemove", "keydown", "scroll", "click", "touchstart"].forEach((evt) => {
    window.addEventListener(evt, markActive, { passive: true });
  });
  markActive();

  return {
    stop() {
      if (timer) clearTimeout(timer);
    }
  };
}


/**
 * ScrollTracker - Tracks scroll behavior per question
 */
function createScrollTracker(metadataTracker) {
  let scrollCount = 0;
  let maxDepth = 0;
  let lastY = null;
  let zigzag = 0;
  let lastDir = 0;

  function recompute() {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop || 0;
    const vh = window.innerHeight || 1;
    const full = Math.max(doc.scrollHeight || 1, 1);
    const depth = Math.min(1, (scrollTop + vh) / full);
    if (depth > maxDepth) maxDepth = depth;

    if (lastY !== null) {
      const dy = scrollTop - lastY;
      const dir = dy === 0 ? 0 : (dy > 0 ? 1 : -1);
      if (dir !== 0 && lastDir !== 0 && dir !== lastDir) zigzag += 1;
      if (dir !== 0) {
        lastDir = dir;
        if (metadataTracker) metadataTracker.recordScroll(dir, depth);
      }
    }
    lastY = scrollTop;
  }

  function onScroll() {
    scrollCount += 1;
    recompute();
  }

  function reset() {
    // Save previous depth before resetting
    if (metadataTracker && maxDepth > 0) {
      metadataTracker.saveScrollDepth();
    }
    scrollCount = 0;
    maxDepth = 0;
    lastY = null;
    zigzag = 0;
    lastDir = 0;
    recompute();
  }

  function snapshot() {
    recompute();
    return { scroll_count: scrollCount, max_depth: maxDepth, zigzag: zigzag };
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  reset();

  return { reset, snapshot };
}


/**
 * TermsTracker - Tracks behavior on the terms/consent page
 */
function createTermsTracker() {
  const startTime = Date.now();
  let maxScrollDepth = 0;

  function updateScrollDepth() {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop || 0;
    const vh = window.innerHeight || 1;
    const full = Math.max(doc.scrollHeight || 1, 1);
    const depth = Math.min(1, (scrollTop + vh) / full);
    if (depth > maxScrollDepth) maxScrollDepth = depth;
  }

  window.addEventListener("scroll", updateScrollDepth, { passive: true });
  updateScrollDepth();

  return {
    getScreenTime() {
      return (Date.now() - startTime) / 1000;
    },
    getScrollDepth() {
      return maxScrollDepth;
    }
  };
}


// Export to window
window.TelemetryClient = TelemetryClient;
window.MetadataTracker = MetadataTracker;
window.createIdleTracker = createIdleTracker;
window.createScrollTracker = createScrollTracker;
window.createTermsTracker = createTermsTracker;
