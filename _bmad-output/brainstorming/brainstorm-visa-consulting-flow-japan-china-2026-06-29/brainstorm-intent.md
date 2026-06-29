# Brainstorm Intent: AI Visa Consulting Flow — Japan & China

---

## 1. Product Vision

An AI-first consumer visa consulting platform for Vietnamese travellers applying to Japan and China, built on top of a licensed agency backend. The product replaces the labour-intensive, fear-driven consulting process with a transparent AI pipeline that screens eligibility, generates conditional document checklists, reviews documents, and monitors embassy requirements — delivering consistent, 24/7 quality at a price point traditional agencies cannot match.

---

## 2. Target Users

**Primary user — Traveller:** Young, tech-savvy Vietnamese travellers who previously couldn't afford or didn't trust traditional visa agencies. Core anxiety: "Is my profile enough to pass?"

**Business partner — Firm owner:** Owner of a licensed visa consulting firm. Core concern: replacing staff cost without losing quality or liability. Proof requirement: see one complete AI conversation and one real approved case.

---

## 3. Core Problem

Visa applicants operate in a fear gap: they don't know if their profile is strong enough, don't trust generic checklists, and contact agencies out of anxiety rather than confidence. The consulting process is entirely human-dependent — staff manually review eligibility, build document lists per profile type, review submissions, and chase embassy updates. This makes the service expensive, inconsistent (case 1 vs. case 1000), and unavailable outside business hours. The emotional job applicants actually need done: *believe they will pass before they pay.*

---

## 4. What AI Replaces

| Step | Current State | AI Role |
|---|---|---|
| Eligibility screening | Human intake call | **Gate**: AI screens profile, denies ineligible cases before payment |
| Document checklist | Staff builds per profile | **Generate**: conditional rules by profile type (employee / student / freelancer) |
| Document review | Staff checks each file | **Review**: rule-based compliance check against profile-specific requirements |
| Embassy requirement monitoring | Manual staff checks | **Monitor**: automated scraping, flags changes to requirements |
| Availability | Business hours only | **24/7**: consistent quality across unlimited concurrent cases |
| Advice / judgment call | Human consultant | **Boundary**: human consultants retain this; AI defers or escalates |

Freelancer profiles are the hardest edge case — variable document types; AI handles with lower confidence, may escalate.

---

## 5. Business Model

**Structure:** B2B2C — the product is a consumer brand; a licensed agency is the invisible backend.

**Positioning:** "We are MoMo" — an AI-first consumer brand layered on top of licensed submission infrastructure. The agency is not marketed; users interact only with the AI brand.

**Pricing lever:** AI eliminates the largest cost (staff) → price below legacy agencies → capture the segment that previously self-excluded due to cost.

**Target segment:** Young tech-savvy travellers. Not the premium segment. Volume + accessibility.

**AI transparency:** Always disclosed. Users know they are talking to AI. This is a feature, not a liability.

---

## 6. Key Constraints

- **Authorized agencies only:** Approximately 12 licensed agencies can submit to the Japan embassy. Partnership with at least one is a hard prerequisite — not optional.
- **Physical submission:** Final submission is physical, handled by the partner agency. AI cannot eliminate this step.
- **Quota rejections:** Strong profiles can be rejected when embassy quota is exhausted. This is outside AI or agency control. Product must set expectation clearly; do not promise approval.
- **Freelancer profiles:** Non-standard document sets make automated review unreliable. Treat as high-effort edge case; may require human escalation in v1.
- **Only accept high-confidence profiles:** Selective intake is a feature. Screening out weak profiles before payment protects brand trust and avoids charging ineligible applicants (a known failure mode of legacy agencies).

---

## 7. Design North Star

**Emotional job: make users believe they will pass.**

Every feature, screen, and interaction is evaluated against this single criterion. The eligibility gate is the most critical UX moment — it is where trust is either earned or lost. A user who passes the eligibility screen has received a signal: *your profile is strong enough*. That signal is the core product value.

Fear reduction is not a UX nicety — it is the mechanism of differentiation.

---

## 8. Go-to-Market

**GTM is one job: win the first approved case and show it.**

- Firm owner trust gate: complete AI conversation log + one real approved case. Without this, no partnership.
- First successful case unlocks: firm owner partnership, user testimonial, product credibility, and the feedback loop for AI improvement.
- Knowledge capture: firm owners and experienced consultants feed cases, outcomes, and reasoning into the system. This is how AI learns approval probability beyond rules.

**Moat:** B2B2C structure + AI transparency = competitors (legacy agencies) are the backend infrastructure. They cannot compete on price or availability, and they cannot replicate the product because they are licensed as a supplier, not a competitor.

---

## 9. MVP Scope

All clusters are Must Have for v1. No phasing.

**Cluster A — AI Pipeline**
- Eligibility gate (pre-payment screen)
- Conditional document checklist (by profile type: employee, student, freelancer)
- Document review (rule-based compliance check)
- Embassy requirement monitoring (automated, flags changes)
- 24/7 availability

**Cluster B — Trust**
- Full AI transparency (disclosed at every touchpoint)
- High-confidence profile filter (selective intake)
- Black box elimination (status visibility after submission)
- First approved case proof (GTM prerequisite)
- Firm owner demo flow (complete conversation walkthrough)

**Cluster C — Business Model**
- B2B2C structure (consumer brand + invisible agency backend)
- One authorized agency partner (Japan submission prerequisite)
- Below-market pricing (enabled by staff cost elimination)
- Young tech-savvy traveller acquisition

**Cluster D — Constraints (accept as given)**
- Hard copy / physical submission handled by partner agency
- Quota rejection out of product scope (set expectation, do not promise)
- Freelancer profile = known hard edge case, handle with lower confidence or escalate

**Cluster E — Emotional Design**
- Every feature reduces fear and builds belief — applied as a design filter, not a separate feature
