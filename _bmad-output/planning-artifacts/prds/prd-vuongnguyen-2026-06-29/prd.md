---
title: AI Visa Consulting Flow — Japan & China
status: final
created: 2026-06-29
updated: 2026-06-29
audience: builder (internal)
---

## 1. Vision

An AI-first consumer visa consulting platform for Vietnamese travellers applying to Japan and China, built on top of a licensed agency backend. The product replaces the labour-intensive, fear-driven consulting process with a transparent AI pipeline that screens eligibility, generates conditional document checklists, reviews submitted documents, and monitors embassy requirements — delivering consistent, 24/7 quality at a price point traditional agencies cannot match.

---

## 2. Problem

### Core friction

Visa applicants operate in a fear gap: they don't know if their profile is strong enough, they don't trust generic checklists, and they contact agencies out of anxiety rather than confidence. The entire consulting process is human-dependent — staff manually review eligibility, build document lists per profile type, check submissions, and chase embassy updates. This makes the service expensive, inconsistent (case 1 vs. case 1000), opaque, and unavailable outside business hours.

### What users actually need

The emotional job-to-be-done is: **believe they will pass before they pay.**

Secondary needs that current agencies fail to meet:

- Know whether their *specific* profile is strong enough (bank balance, employment type, travel history)
- Know exactly which documents they need — not a generic checklist, but one conditional on their profile
- Know the bank balance threshold for their situation — the #1 unaddressed anxiety in the market
- Have visibility on status after submission (right now: total silence)
- Be able to ask questions at midnight, not at 9am when the agency opens

### What agencies do wrong

Traditional agencies (VDAS, iStar, Visa Việt, and others):
- Accept ineligible profiles and charge them anyway — the most common complaint
- Give the same generic document list regardless of employment type
- Communicate via Zalo/WhatsApp — no audit trail, inconsistent answers
- Hold original documents (employment letters, bank books) for weeks
- Provide no updates after hard copy submission
- Cannot serve outside business hours

No tech-first competitor exists in this market. Global platforms (VisaHQ, iVisa) don't operate here — they focus on e-visa countries; Japan and China for Vietnamese applicants require physical submission, outside those platforms' model.

---

## 3. Users

### Primary user — Traveller

Young, tech-savvy Vietnamese travellers who:
- Are applying for Japan or China for the first time, OR
- Have applied before but faced friction (rejection, confusing docs, high fees)
- Core anxiety: "Is my profile / bank statement enough to pass?"
- Cannot afford or distrust traditional agencies
- Are comfortable with AI-first interfaces

**Not** targeting premium travellers who already have strong relationships with agencies.

### Applicant profile types

| Type | Common | Friction level | Notes |
|---|---|---|---|
| Salaried employee | Most common | Low-medium | Needs employment certificate, payslip, day-off letter matching travel dates |
| Student (under 18 or in university) | Common | Medium | Needs parent guarantee letter + parent financial docs |
| Business owner (registered) | Medium | Medium | Business license + company financials, not just personal bank statement |
| Freelancer / self-employed (informal) | Less common | **High** | No standard docs; must prove income via contracts, bank statements, tax records — AI handles with lower confidence |
| Housewife / homemaker | Less common | Medium | Depends on spouse's financial docs; "dependent" profile |
| Retired | Less common | Low-medium | Pension docs + bank statement; growing segment |
| Returning traveller (prior Japan/China stamps) | Medium | Low | Prior travel history significantly improves approval odds; AI should apply higher confidence score |
| Group / family application | Common | Medium-high | Individual profiles interact — weak member may affect group; compound assessment needed |

### Partner user — Firm owner

Owner of a licensed visa consulting firm (one of ~12 authorized to submit to Japan embassy). Core concerns:
- Replace staff cost without losing submission quality or liability
- See that AI is trustworthy before committing (proof requirement: one complete AI conversation + one real approved case)
- Maintain their authorized submitter status (they are the licensed backend; the product is the consumer brand)

---

## 4. Competitive Landscape

### Competitor map

| Type | Who | Positioning | Weakness |
|---|---|---|---|
| Traditional agencies | VDAS, iStar Visa, Visa Việt, 50+ local shops | "We handle everything" | All-human, business hours only, inconsistent, opaque, charge ineligible profiles |
| Semi-online | Most agencies now have websites + Zalo | Slightly more accessible | Digital = web form + WhatsApp. Still fully human backend. |
| Global tech | VisaHQ, iVisa | Tech-first, scalable | Don't serve Vietnam→Japan/China (physical submission requirement outside their model) |
| AI-native | **None** | — | Gap in market |

### Positioning

Price below market (possible because AI eliminates the largest cost: staff). Serve the segment traditional agencies don't want — first-timers, tech-savvy users, anyone priced out of premium agencies.

The moat is structural: licensed agencies are the backend infrastructure. They can't compete on price or availability, and they can't replicate the product because they are the supplier, not the competitor.

---

## 5. What AI Replaces

| Step | Current state | AI role | Confidence |
|---|---|---|---|
| Eligibility screening | Human intake call or consultation | **Gate**: AI screens profile before payment, denies ineligible cases | High |
| Prior denial screening | Nobody checks this before charging the applicant | **Gate**: AI screens for prior denials and reapplication bans before payment | High |
| Document checklist | Staff builds per profile, inconsistent | **Generate**: conditional rules by profile type | High |
| Document review | Staff checks each file manually | **Review**: rule-based compliance check against profile-specific requirements | High |
| Embassy requirement monitoring | Manual staff checks, often missed | **Monitor**: automated scraping, flags requirement changes | High |
| Application status updates | Nothing (total black box) | **Notify**: status updates at each stage (received, submitted, in review, decided) | Medium |
| 24/7 availability | Business hours only | **Always on**: consistent quality, unlimited concurrent cases | High |
| Advice / judgment calls | Human consultant | **Boundary**: AI defers or escalates; human consultants retain this role | N/A |

---

## 6. Feature Requirements

### FR-A: Eligibility Gate (pre-payment)

**FR-A1.** System collects applicant profile data: destination (Japan / China), employment type, prior denial history, travel history (prior Japan/China stamps), travel dates, passport expiry.

**FR-A2.** System evaluates profile against structural eligibility signals for the requested visa type. Signals assessed: employment type (determines which anchor documents can exist), prior denial recency (Japan 6-month reapplication ban), travel date feasibility (processing time + document prep), passport validity.

**FR-A3.** System returns one of three outcomes:
- Eligible — proceed to travel date confirmation and payment
- Likely eligible, edge case — proceed with explicit lower-confidence flag and optional human escalation
- Not eligible — blocked pre-payment, specific reason stated, no charge

**FR-A4.** System does NOT state specific financial thresholds or coach financial preparation. Embassy rules prohibit this; no official minimum bank balance exists. System assesses profile structure only — whether the applicant's employment type allows anchor documents to exist, not whether their finances are "sufficient."

**FR-A5.** Prior denial gate: if applicant was denied a Japan visa within the last 6 months, system blocks the application and explains the reapplication waiting period. Same logic applies to China if denial was recent.

**FR-A6.** If profile type is Freelancer or informal self-employed, system flags as high-effort edge case with lower confidence score, offers option to escalate to human review.

**FR-A7.** Returning travellers with prior Japan/China stamps receive a higher confidence signal; system surfaces this to the user as a positive indicator.

**FR-A8.** Group/family applications are assessed as a compound profile; system evaluates how each member's profile interacts and flags if any member has a structural gap.

### FR-B: Conditional Document Checklist

**FR-B1.** After eligibility pass, system generates a document checklist specific to the applicant's profile type and visa category.

**FR-B2.** Checklist is conditional — different requirements rendered per profile type (see profile table above). No generic list presented to any user.

**FR-B3.** Each checklist item includes: document name, what it must contain, acceptable format (original / scan / certified copy), and why it is required (plain-language explanation).

**FR-B4.** For Employee profile: checklist includes leave approval letter and explicitly requires that stated travel dates match the travel dates on the visa application.

**FR-B5.** For Student profile: checklist includes parent guarantee letter template and specifies that parent's financial documents must accompany.

**FR-B6.** For Freelancer profile: checklist is advisory (AI offers the most common document set for informal workers); user is warned that officer judgment applies and confidence is lower.

**FR-B7.** Checklist updates automatically if embassy requirements change (fed by FR-E monitoring).

### FR-C: Document Review

**FR-C1.** Applicant uploads documents against each checklist item.

**FR-C2.** System reviews each uploaded document for: completeness, required fields present, date validity, consistency with stated profile (e.g., travel dates on leave letter match application dates).

**FR-C3.** System returns per-document status: Pass / Fail / Needs Clarification, with specific failure reason.

**FR-C4.** System surfaces an overall readiness score before submission: "Your documents look ready" / "X issues to resolve before we submit."

**FR-C5.** Freelancer/edge-case profiles: review confidence is stated explicitly ("AI review confidence: medium — a human will perform a secondary check before submission").

**FR-C6.** System never approves submission for a profile it flagged as ineligible in FR-A. Gate cannot be bypassed.

### FR-D: Status Tracking

**FR-D1.** After hard copy submission by partner agency, applicant receives status updates at each stage: documents received by agency / documents submitted to embassy / result received.

**FR-D2.** Result notification: approved (with pickup instructions) or rejected (with stated reason where embassy provides one).

**FR-D3.** If quota rejection (strong profile but embassy quota exhausted), system communicates this specifically — differentiates from profile-based rejection. Does not suggest reapplication without clarifying what the user can do.

### FR-E: Embassy Requirement Monitoring

**FR-E1.** System monitors Japan embassy Vietnam website and China embassy Vietnam website for changes to visa requirements, fee schedules, and accepted document types.

**FR-E2.** When a change is detected, system flags affected in-progress applications and updates checklists for new applications.

**FR-E3.** Internal alert to operator when a monitored change is detected.

### FR-F: Trust & Transparency

**FR-F1.** Every user-facing interaction discloses that they are talking to an AI system. Disclosure is explicit on first session, persistent in UI — not buried in fine print.

**FR-F2.** Eligibility gate result includes a plain-language explanation of how the decision was reached (not a black box).

**FR-F3.** Confidence levels are surfaced to the user at eligibility screening and document review — not hidden.

**FR-F4.** Product never promises approval. Language consistently frames outcomes as "high chance" / "meets requirements" — not "guaranteed."

**FR-F5.** Firm owner demo flow: a complete walkthrough of one full AI conversation (eligibility → checklist → document review) is available for the agency partner to review before committing to partnership.

---

## 7. Business Model

**Structure:** B2B2C — product owns the consumer brand; one authorized agency is the invisible licensed backend.

**Consumer brand:** AI-first. Users interact only with the product brand. Partner agency is not marketed. This is the MoMo model: users know MoMo, not which bank.

**Revenue:** Service fee per successful submission (collected from user). Price below market average.

**Cost structure:** AI eliminates the dominant cost (staff). Physical submission is the only human-labour step, handled by partner agency at agreed-upon per-case fee.

**GTM prerequisite:** Partnership with at least one authorized agency before launch. No agency = no legal submission capability = no product.

**First customer:** Not from ads. From the firm owner demo — one complete conversation log + one real approved case. This is the proof asset that unlocks everything.

---

## 8. Constraints

| Constraint | Nature | Implication |
|---|---|---|
| ~12 authorized agencies for Japan submission | Hard market constraint | Must partner with one before launch. Non-negotiable. |
| Physical hard copy submission | Process constraint | AI cannot eliminate this step. Partner agency handles it. |
| Embassy quota rejection | External constraint | Product sets expectation clearly; does not promise approval. When quota rejection occurs, system communicates it as a structural event, not a product failure. |
| Freelancer profile complexity | Technical constraint | Variable document sets; AI review reliability lower. v1 handles with explicit lower-confidence flag + option to escalate. |
| China biometric requirement | Process constraint | Applicants must appear in person at China embassy for fingerprinting. AI cannot handle this; product directs user to embassy appointment step. |
| AI transparency | Design constraint | Cannot disguise AI as human. Users must always know they are interacting with AI. |

---

## 9. Non-Functional Requirements

**NFR-1 Availability.** System must be available 24/7. Downtime window: max 30 minutes/month.

**NFR-2 Latency.** Eligibility gate response: under 10 seconds. Document checklist generation: under 5 seconds.

**NFR-3 Data handling.** Applicant documents (identity documents, financial records) are sensitive PII. Must not be stored longer than necessary for the active application. Storage and access to be scoped to minimum required.

**NFR-4 AI accuracy.** Document review checks are rule-based (not LLM hallucination risk). Eligibility gate rules must be auditable and version-controlled. Any rules change must be logged with date and reason.

**NFR-5 Escalation path.** For every AI decision, a human-review escalation path must exist. This is especially required for: Freelancer profiles, edge-case eligibility outcomes, and FR-D2 rejection notifications.

**NFR-6 Language.** All user-facing content in Vietnamese. Internal admin/operator tools may be English.

---

## 10. Success Metrics

| Metric | What it measures | Target (v1) |
|---|---|---|
| First approved case | Core GTM proof asset | 1 approved case before any marketing spend |
| Eligibility gate accuracy | Profiles approved through gate that were then submitted successfully | > 90% submission rate on gated profiles |
| False positive rate | Ineligible profiles that passed the gate | < 5% (protect brand trust) |
| Document review catch rate | Document issues caught before submission vs. issues caught by embassy | > 85% catch rate |
| User satisfaction at eligibility gate | NPS / survey at gate decision point | > 60 NPS |
| Agency partner sign-up | B2B prerequisite | 1 signed agency before launch |
| Time-to-checklist | Time from profile input to checklist generated | < 2 minutes end-to-end |

**Counter-metrics (watch for)**
- Gate too strict → high denial rate of borderline-but-approvable profiles → lost revenue
- Gate too loose → profile submitted that gets rejected → damages brand trust
- Review too slow → user drops off before document upload complete

---

## 11. Open Questions

| Question | Priority | Owner | Resolution condition |
|---|---|---|---|
| What structural profile signals are most predictive of approval, per agency partner's case experience? | High | Builder (interview with agency partner) | Confirmed before eligibility gate rules are written |
| How does the authorized agency partnership work legally — are there service agreements, liability clauses? | High | Builder (legal) | Resolved before first live submission |
| Does the partner agency charge per-case or revenue share? What's the unit economics? | High | Builder (negotiation) | Agreed before pricing is set publicly |
| For China visa: does the product need to handle biometric appointment booking? | Medium | Builder | Confirmed with China embassy process research |
| For group applications: does the embassy assess joint profiles or individual? | Medium | Builder (research) | Confirmed by agency partner |
| Will the firm owner accept AI transparency as a product feature, or will it be a dealbreaker? | High | Builder (conversation with firm owner) | Resolved in first firm owner meeting |
| What happens to in-progress applications if the agency partner relationship ends? | Low | Builder (legal/ops) | Addressed in partnership agreement |
