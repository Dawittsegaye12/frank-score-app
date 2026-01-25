# All Personas Summary

## Total Personas: 11

All personas use password: **password123**

---

## LOW RISK (PD < 0.3)
**0 personas**

---

## MEDIUM RISK (0.3 <= PD < 0.6)
**5 personas**

1. **charlie** (ID: 3)
   - Email: charlie@example.com
   - PD: 0.3425 (34.25%)
   - Type: Low Risk Persona

2. **bob** (ID: 2)
   - Email: bob@example.com
   - PD: 0.3821 (38.21%)
   - Type: Low Risk Persona

3. **alice** (ID: 1)
   - Email: alice@example.com
   - PD: 0.4355 (43.55%)
   - Type: Low Risk Persona
   - Previous Loans: 5.0
   - Total Amount: 41,867.66
   - Daily Burden: 1,560.68

4. **eve** (ID: 5)
   - Email: eve@example.com
   - PD: 0.4408 (44.08%)
   - Type: Medium Risk Persona

5. **john** (ID: 10)
   - Email: john@example.com
   - PD: 0.4604 (46.04%)
   - Type: New User Persona

---

## HIGH RISK (PD >= 0.6)
**6 personas**

1. **frank** (ID: 6)
   - Email: frank@example.com
   - PD: 0.6038 (60.38%)
   - Type: Medium Risk Persona

2. **diana** (ID: 4)
   - Email: diana@example.com
   - PD: 0.6958 (69.58%)
   - Type: Medium Risk Persona

3. **jane** (ID: 11)
   - Email: jane@example.com
   - PD: 0.9479 (94.79%)
   - Type: New User Persona
   - Previous Loans: 0
   - Total Amount: 20,131.36
   - Daily Burden: 1,672.97

4. **grace** (ID: 7)
   - Email: grace@example.com
   - PD: 1.0000 (100.00%)
   - Type: High Risk Persona

5. **henry** (ID: 8)
   - Email: henry@example.com
   - PD: 1.0000 (100.00%)
   - Type: High Risk Persona

6. **ivy** (ID: 9)
   - Email: ivy@example.com
   - PD: 1.0000 (100.00%)
   - Type: High Risk Persona

---

## Notes

- All PD values are calculated using the **fallback heuristic** method due to model version incompatibility
- The Random Forest model fails due to scikit-learn version mismatch (trained with 1.4.2, current is 1.8.0)
- For accurate predictions, retrain the model with the current scikit-learn version
- Fallback calculation uses: `burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2`

---

## Quick Reference

**Low Risk Personas (originally):**
- alice, bob, charlie

**Medium Risk Personas (originally):**
- diana, eve, frank

**High Risk Personas (originally):**
- grace, henry, ivy

**New User Personas:**
- john, jane




