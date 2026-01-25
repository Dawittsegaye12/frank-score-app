(function () {
  const qBox = document.getElementById("qBox");
  const status = document.getElementById("status");
  const qIndex = document.getElementById("qIndex");
  const qText = document.getElementById("qText");
  const optionsContainer = document.getElementById("options");
  const err = document.getElementById("err");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");

  function setErr(msg) { err.textContent = msg || ""; }
  function setStatus(msg) { status.textContent = msg || ""; }

  const url = new URL(window.location.href);
  const assessmentId = url.searchParams.get("assessment_id");
  if (!assessmentId) {
    setErr("Missing assessment_id.");
    return;
  }

  const sessionId = sessionStorage.getItem(`fs_session_${assessmentId}`);
  if (!sessionId) {
    setErr("Missing session_id (start from /terms).");
    return;
  }
  const consentFin = sessionStorage.getItem(`fs_consent_fin_${assessmentId}`) === "1";

  // Initialize telemetry and metadata tracking
  const telemetry = new window.TelemetryClient({ assessmentId, sessionId });
  const metadataTracker = new window.MetadataTracker(assessmentId);
  const idle = window.createIdleTracker(telemetry, metadataTracker, { thresholdMs: 10000 });
  const scrollTracker = window.createScrollTracker(metadataTracker);

  // Load terms data from session storage (set by terms page)
  const termsScreenTime = parseFloat(sessionStorage.getItem(`fs_terms_time_${assessmentId}`) || "0");
  const termsScrollDepth = parseFloat(sessionStorage.getItem(`fs_terms_scroll_${assessmentId}`) || "0");
  metadataTracker.setTermsData(termsScreenTime, termsScrollDepth);

  let questions = [];
  let idx = 0;
  const answers = {}; // item_id -> selected_option ("A"/"B"/"C"/"D")
  let prevSelected = null;

  function getSelected() {
    const el = document.querySelector('input[name="option"]:checked');
    return el ? el.value : null;
  }

  function setSelected(option) {
    document.querySelectorAll('input[name="option"]').forEach((r) => {
      r.checked = r.value === option;
    });
  }

  function clearSelected() {
    document.querySelectorAll('input[name="option"]').forEach((r) => (r.checked = false));
  }

  function itemId() {
    return questions[idx] ? questions[idx].item_id : null;
  }

  function emitScrollSummary(leavingItemId) {
    const snap = scrollTracker.snapshot();
    telemetry.track("scroll_summary", snap, leavingItemId);
  }

  function renderOptions(q) {
    optionsContainer.innerHTML = "";

    if (!q.options || typeof q.options !== "object") {
      optionsContainer.innerHTML = "<p class='error'>No options available for this question.</p>";
      return;
    }

    const optionLetters = ["A", "B", "C", "D"];
    optionLetters.forEach((letter) => {
      const optionText = q.options[letter];
      if (!optionText) return;

      const label = document.createElement("label");
      label.className = "option-label";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "option";
      radio.value = letter;
      radio.id = `option_${letter}`;

      const textSpan = document.createElement("span");
      textSpan.className = "option-text";
      textSpan.textContent = optionText;

      label.appendChild(radio);
      label.appendChild(document.createTextNode(` ${letter}. `));
      label.appendChild(textSpan);

      optionsContainer.appendChild(label);
    });

    // Add event listeners for option changes
    document.querySelectorAll('input[name="option"]').forEach((r) => {
      r.addEventListener("change", () => {
        const q = questions[idx];
        if (!q) return;
        const v = getSelected();

        // Record click and first interaction for hesitation
        metadataTracker.recordClick();
        metadataTracker.recordFirstInteraction(q.item_id);
        metadataTracker.recordAnswerSelect(q.item_id, v);

        telemetry.track("answer_select", { value: v, option: v }, q.item_id);

        if (prevSelected !== null && v !== prevSelected) {
          telemetry.track("answer_change", { from: prevSelected, to: v }, q.item_id);
          metadataTracker.recordAnswerChange(q.item_id, prevSelected, v);
        }
        prevSelected = v;
      });
    });
  }

  function render() {
    setErr("");
    const q = questions[idx];
    if (!q) return;

    // Update progress bar
    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");
    const progressPercent = document.getElementById("progressPercent");
    const percent = Math.round(((idx + 1) / questions.length) * 100);
    if (progressBar) progressBar.style.width = percent + "%";
    if (progressText) progressText.textContent = `Question ${idx + 1} of ${questions.length}`;
    if (progressPercent) progressPercent.textContent = percent + "%";

    qIndex.textContent = `Question ${idx + 1} of ${questions.length}`;
    qText.textContent = q.prompt || q.text || "";
    prevBtn.disabled = idx === 0;
    nextBtn.textContent = (idx === questions.length - 1) ? (consentFin ? "Continue" : "Finish") : "Next";

    renderOptions(q);

    const saved = answers[q.item_id];
    if (saved) setSelected(saved);
    else clearSelected();
    prevSelected = getSelected();

    scrollTracker.reset();

    // Record question view for timing
    metadataTracker.recordQuestionView(q.item_id);
    telemetry.track("question_view", { index: idx }, q.item_id);
  }

  async function saveAnswer(item_id, selected_option) {
    const payload = {
      assessment_id: assessmentId,
      item_id: item_id,
      selected_option: selected_option,
      answered_at_ms: Date.now()
    };
    const res = await fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
  }

  async function completeAndGoResult() {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'questions.js:163', message: 'completeAndGoResult entry', data: { questionsLength: questions.length }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'B' }) }).catch(() => { });
    // #endregion
    // Mark assessment as completed
    metadataTracker.markCompleted();

    // Compute final metadata and emit as event
    const finalMetadata = metadataTracker.computeMetadata(questions.length);
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/d7df77e8-d17a-4f54-8029-c8a7bd228002', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'questions.js:168', message: 'metadata_summary before track', data: { finalMetadataKeys: Object.keys(finalMetadata).length, hasCompletionStatus: !!finalMetadata.completion_status, hasAvgResponseTime: finalMetadata.avg_response_time_sec !== null }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'B' }) }).catch(() => { });
    // #endregion
    telemetry.track("metadata_summary", finalMetadata, null);

    telemetry.track("assessment_end", {}, null);
    // Flush events reliably and AWAIT them to ensure they are in DB before scoring starts
    // Do NOT use flushBeacon() here because it clears the queue and sends async, 
    // causing a race where api/complete runs before events are saved.
    try {
      await telemetry.flush();
    } catch (e) {
      console.error("Failed to flush telemetry:", e);
    }

    const res = await fetch("/api/complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ assessment_id: assessmentId })
    });
    if (!res.ok) throw new Error(await res.text());
    window.location.href = `/result?assessment_id=${encodeURIComponent(assessmentId)}`;
  }

  async function goFinancial() {
    // Mark as completed and send metadata_summary before going to financial page
    // The financial page will call /api/complete, but we need to send the correct metadata first
    metadataTracker.markCompleted();
    const finalMetadata = metadataTracker.computeMetadata(questions.length);
    telemetry.track("metadata_summary", finalMetadata, null);
    telemetry.track("assessment_end", { next: "financial" }, null);
    // Flush events before navigation
    telemetry.flushBeacon();
    await telemetry.flush();
    window.location.href = `/financial?assessment_id=${encodeURIComponent(assessmentId)}`;
  }

  prevBtn.addEventListener("click", () => {
    if (idx === 0) return;
    telemetry.track("page_nav", { direction: "back", via: "prev_button" }, itemId());
    metadataTracker.recordBackNav();
    emitScrollSummary(itemId());
    idx -= 1;
    render();
  });

  nextBtn.addEventListener("click", async () => {
    setErr("");
    const q = questions[idx];
    if (!q) return;

    const v = getSelected();
    if (v === null) {
      setErr("Please select an option (A, B, C, or D).");
      metadataTracker.recordSkip(q.item_id);
      return;
    }

    nextBtn.disabled = true;
    prevBtn.disabled = true;
    setStatus("Saving…");
    try {
      const prior = answers[q.item_id];
      if (prior !== undefined && prior !== v) {
        telemetry.track("answer_change", { from: prior, to: v, via: "next" }, q.item_id);
        metadataTracker.recordAnswerChange(q.item_id, prior, v);
      }
      answers[q.item_id] = v;

      telemetry.track("answer_submit", { value: v, option: v }, q.item_id);
      metadataTracker.recordAnswerSubmit(q.item_id);
      await saveAnswer(q.item_id, v);
      emitScrollSummary(q.item_id);

      if (idx < questions.length - 1) {
        idx += 1;
        render();
      } else {
        setStatus("Computing…");
        // In v2, we use persona financial data, so skip financial page
        // Always go directly to results
        await completeAndGoResult();
      }
    } catch (e) {
      setErr(String(e && e.message ? e.message : e));
    } finally {
      nextBtn.disabled = false;
      prevBtn.disabled = idx === 0;
      setStatus("");
    }
  });

  // Navigation telemetry
  window.addEventListener("popstate", () => {
    telemetry.track("page_nav", { direction: "back" }, itemId());
    metadataTracker.recordBackNav();
  });

  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      telemetry.track("page_nav", { direction: "hidden" }, itemId());
      telemetry.flushBeacon();
    }
  });

  (async () => {
    try {
      setStatus("Loading questions…");
      telemetry.track("assessment_start", { path: window.location.pathname }, null);
      const res = await fetch(`/api/questions?assessment_id=${encodeURIComponent(assessmentId)}`);
      if (!res.ok) throw new Error(await res.text());
      questions = await res.json();
      if (!Array.isArray(questions) || questions.length === 0) {
        throw new Error("No questions returned.");
      }
      setStatus("");
      render();
    } catch (e) {
      setErr(String(e && e.message ? e.message : e));
      setStatus("");
    }
  })();
})();
