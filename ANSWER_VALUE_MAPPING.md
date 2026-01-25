# Answer Value Mapping for All Questions

## Overview
Each question has 4 options (A, B, C, D) that are mapped to numeric values ranging from **0 to 3**:
- **0** = weakest/highest risk behavior
- **1** = low/moderate risk
- **2** = moderate/good behavior  
- **3** = strongest/most protective behavior

---

## Question 1: Conscientiousness
**Prompt:** You notice a small mismatch in your daily records.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Re-check the last step before sending anything out. |
| **A** | **2** | Mark it and continue; you will reconcile it later. |
| **D** | **1** | Ask someone if they have seen the same issue. |
| **C** | **0** | Assume it is normal variation and keep going. |

---

## Question 2: Impulsivity
**Prompt:** A "today-only" deal pops up while you are tired.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Add it to cart and decide tomorrow. |
| **D** | **2** | Close it and check your budget before deciding. |
| **A** | **1** | Buy now, but keep it within a strict limit. |
| **C** | **0** | Buy now; you can adjust later if needed. |

---

## Question 3: Financial Self-Confidence
**Prompt:** A loan term is unclear but the process is moving fast.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **C** | **3** | Ask until you feel comfortable enough to explain it back. |
| **B** | **2** | Ask one question, then proceed. |
| **D** | **1** | Ask a friend later and decide after that. |
| **A** | **0** | Sign and learn later; speed matters. |

---

## Question 4: Planning Horizon
**Prompt:** You can earn more this week, but it may create a problem next month.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **C** | **3** | Choose stability even if it means less now. |
| **B** | **2** | Take it only if you can still cover next month. |
| **A** | **1** | Take the extra earnings now and handle later. |
| **D** | **0** | Take it and hope it works out. |

---

## Question 5: Self-Control
**Prompt:** You promised yourself "no borrowing this month," but a temptation appears.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **D** | **3** | Stick to the rule unless it is a true emergency. |
| **C** | **2** | Try to adjust spending first, then decide. |
| **B** | **1** | Borrow if the reason feels justified. |
| **A** | **0** | Borrow a small amount; it won't matter. |

---

## Question 6: Locus of Control
**Prompt:** A plan fails and you lose time.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | There is always something you can change next time. |
| **D** | **2** | Partly luck, partly choices; you can adjust. |
| **A** | **1** | Mostly bad luck; it happens. |
| **C** | **0** | It was unavoidable; nothing could help. |

---

## Question 7: Honesty
**Prompt:** You can slightly exaggerate income and likely benefit.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **C** | **3** | Report honestly, but round if needed and explain. |
| **D** | **2** | Avoid giving a number and let them decide. |
| **B** | **1** | Adjust it a little if it helps. |
| **A** | **0** | Adjust it upward; everyone does it. |

---

## Question 8: Integrity / Rule Following
**Prompt:** Someone suggests a "small gift" to speed a process.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **D** | **3** | Refuse and use the proper process. |
| **C** | **2** | Avoid if possible and look for normal options. |
| **B** | **1** | Accept only if you are truly stuck. |
| **A** | **0** | Accept; speed is worth it. |

---

## Question 9: Obligation to Repay
**Prompt:** Payment is due today but you are short.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Pay what you can and communicate a clear plan early. |
| **D** | **2** | Pay partially and hope they understand. |
| **C** | **1** | Pay late and explain later. |
| **A** | **0** | Say nothing and pay late. |

---

## Question 10: Grit / Perseverance
**Prompt:** A goal becomes boring.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **C** | **3** | Continue steadily with small steps. |
| **B** | **2** | Continue only when motivated. |
| **D** | **1** | Pause for a while and see later. |
| **A** | **0** | Quit and switch goals. |

---

## Question 11: Present Bias / Time Preference
**Prompt:** You can get 100 today or 130 next month.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **D** | **3** | Take next month; planning matters. |
| **B** | **2** | Take next month unless you urgently need today. |
| **C** | **1** | Take today, but only if you planned for it. |
| **A** | **0** | Take today; future is uncertain. |

---

## Question 12: Risk Attitude
**Prompt:** Choose: sure 90 vs 50% chance of 180.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **C** | **3** | Choose based on your buffer and obligations. |
| **B** | **2** | Choose sure; predictability matters. |
| **D** | **1** | Choose gamble when you feel confident. |
| **A** | **0** | Choose the gamble; upside matters. |

---

## Question 13: Financial Decision Quality
**Prompt:** Two loans: one low monthly, one low total.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Choose the one with the lowest total cost and manageable risk. |
| **A** | **2** | Choose the one with the lowest monthly payment. |
| **C** | **1** | Choose the one that feels simpler. |
| **D** | **0** | Choose quickly; both are fine. |

---

## Question 14: Spending vs Saving Orientation
**Prompt:** You get extra income.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Save first, then decide on a small treat. |
| **C** | **2** | Split: some spending, some saving. |
| **D** | **1** | Spend most now; saving can start later. |
| **A** | **0** | Spend it; extra money is for life. |

---

## Question 15: Commitment / Follow-through
**Prompt:** You promised delivery Friday; work becomes harder midweek.

| Option | Value | Answer Text |
|--------|-------|-------------|
| **B** | **3** | Inform early and propose a realistic plan. |
| **C** | **2** | Deliver part and explain after. |
| **D** | **1** | Delay and hope it's forgiven. |
| **A** | **0** | Stay quiet and deliver late. |

---

## How Scores Are Used

1. **Raw Score Calculation**: For each trait, the system averages the scores from answered questions
2. **Normalization**: The average is divided by 3.0 to normalize to [0, 1] range
3. **Final Trait Score**: Combined with behavior-based traits using the formula:
   ```
   Trait_final = 0.6 × Trait_behaviour + 0.4 × Trait_content
   ```

---

*Generated from: `questiondb/psychometric_question_bank_v2_admin.json`*

