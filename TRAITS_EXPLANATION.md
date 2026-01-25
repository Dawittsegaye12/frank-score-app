# Traits Calculated After Assessment

## Overview
After completing the psychometric assessment, **15 traits** are calculated and displayed on the result page.

## Where to See Traits
1. **Result Page**: After completing the assessment, go to `/result?assessment_id=FSxxxxxx`
2. **Section**: "Traits (trait_final)" - displayed with visual bars and numeric values
3. **API Endpoint**: `GET /api/result?assessment_id=FSxxxxxx` returns `trait_final` object

## The 15 Traits

1. **conscientiousness**
   - Measures reliability, organization, and follow-through
   - Based on: completion status, sessions, skip rate, idle time, response time

2. **impulsivity**
   - Measures tendency to act without thinking
   - Based on: rapid clicks, answer changes, hesitation time
   - Note: Lower impulsivity is better for credit

3. **financial_self_confidence**
   - Measures confidence in financial decision-making
   - Based on: financial item hesitation, response time, completion

4. **planning_horizon**
   - Measures ability to think long-term
   - Based on: terms reading time, scroll engagement, response time, idle time

5. **self_control**
   - Measures ability to resist impulses
   - Based on: rapid clicks, answer changes, idle time

6. **locus_of_control**
   - Measures belief in personal control vs. external factors
   - Based on: completion, sessions, back navigation

7. **honesty**
   - Measures truthfulness and consistency
   - Based on: inconsistency score, skip rate, extreme option rate

8. **integrity_rule_following**
   - Measures adherence to rules and instructions
   - Based on: terms reading, compliance flags, skip rate

9. **obligation_to_repay**
   - Measures sense of responsibility to repay debts
   - Based on: completion, scroll engagement, terms reading

10. **grit_perseverance**
    - Measures persistence and resilience
    - Based on: completion, sessions, response engagement, idle time

11. **present_bias_time_preference**
    - Measures preference for immediate vs. future rewards
    - Based on: hesitation, answer changes, response time

12. **risk_attitude**
    - Measures risk tolerance
    - Based on: extreme option rate (moderate risk is balanced)

13. **financial_decision_quality**
    - Measures quality of financial decision-making
    - Based on: response time on financial items, hesitation, engagement

14. **spending_vs_saving** (or **spending_vs_saving_orientation**)
    - Measures orientation toward saving vs. spending
    - Based on: terms reading (careful reader), hesitation, idle time
    - Higher = saving orientation

15. **commitment_follow_through**
    - Measures ability to complete commitments
    - Based on: completion, sessions, compliance

## How Traits Are Calculated

Each trait is computed using a **three-body model**:

1. **Content Traits** (40% weight)
   - Derived from explicit answers to questions
   - Each question maps to a trait
   - Answers (A/B/C/D) are converted to scores (0-3) and normalized

2. **Behavior Traits** (60% weight)
   - Derived from 30 metadata features tracked during assessment
   - Includes: response times, hesitation, scroll behavior, idle time, etc.

3. **Final Trait** (Combined)
   ```
   Trait_final = 0.6 × Trait_behaviour + 0.4 × Trait_content
   ```

## Trait Values

- **Range**: 0.0 to 1.0 (normalized)
- **Display**: 
  - Visual bar (0-100% width)
  - Numeric value (4 decimal places, e.g., 0.6910)
- **Interpretation**:
  - Higher values generally indicate better creditworthiness
  - Values are relative and should be interpreted in context

## Example Result

After assessment, you'll see something like:
```
Traits (trait_final)
├─ commitment_follow_through: 0.7600 [████████████████████]
├─ conscientiousness: 0.6910 [██████████████████]
├─ financial_decision_quality: 0.7332 [███████████████████]
├─ financial_self_confidence: 0.5667 [████████████]
├─ grit_perseverance: 0.7804 [████████████████████]
├─ honesty: 0.6500 [████████████████]
├─ impulsivity: 0.4733 [█████████]
├─ integrity_rule_following: 0.7821 [████████████████████]
├─ locus_of_control: 0.6267 [███████████████]
├─ obligation_to_repay: 0.5819 [████████████]
├─ planning_horizon: 0.8969 [██████████████████████]
├─ present_bias_time_preference: 0.6067 [██████████████]
├─ risk_attitude: 0.7500 [███████████████████]
├─ self_control: 0.7872 [████████████████████]
└─ spending_vs_saving_orientation: 0.5667 [████████████]
```

## API Response Format

```json
{
  "assessment_id": "FS000011",
  "trait_final": {
    "conscientiousness": 0.6910,
    "impulsivity": 0.4733,
    "financial_self_confidence": 0.5667,
    "planning_horizon": 0.8969,
    "self_control": 0.7872,
    "locus_of_control": 0.6267,
    "honesty": 0.6500,
    "integrity_rule_following": 0.7821,
    "obligation_to_repay": 0.5819,
    "grit_perseverance": 0.7804,
    "present_bias_time_preference": 0.6067,
    "risk_attitude": 0.7500,
    "financial_decision_quality": 0.7332,
    "spending_vs_saving_orientation": 0.5667,
    "commitment_follow_through": 0.7600
  },
  "pd_psych_hat": 0.9177,
  "pd_fin_hat": 0.5991,
  "pd_final_hat": 0.7265,
  "metadata": { ... }
}
```

