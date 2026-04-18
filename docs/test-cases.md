# Test Cases (TC1–TC8)

This page supports Milestone 4 by providing reproducible inputs and expected outputs for the Processing rules.

## Output Fields

- `status`: `APPROVED | NEEDS_REVISION | INCOMPLETE`
- `category`: `OPPORTUNITY | ACADEMIC | SOCIAL | GENERAL`
- `priority`: `HIGH | MEDIUM | NORMAL`
- `note`: short explanation for UI display

## Case Table

| TC | Purpose | Input (key point) | Expected Output | Rule Basis |
|---|---|---|---|---|
| TC1 | Missing required fields has highest precedence | missing `organiser` | `INCOMPLETE`, `OPPORTUNITY`, `HIGH`, note mentions missing field | Missing required field → `INCOMPLETE` (overrides other rules) |
| TC2 | Date format validation | `date=2026-4-17` | `NEEDS_REVISION`, `GENERAL`, `NORMAL`, note indicates date format | Date not in `YYYY-MM-DD` → `NEEDS_REVISION` |
| TC3 | Description length validation | `description` < 40 | `NEEDS_REVISION`, `GENERAL`, `NORMAL`, note indicates min length | Description < 40 → `NEEDS_REVISION` |
| TC4 | General event approval | valid input, no keywords | `APPROVED`, `GENERAL`, `NORMAL`, note=`Approved` | All checks pass → `APPROVED` |
| TC5 | Opportunity category + priority | contains `career`/`internship`/`recruitment` | `APPROVED`, `OPPORTUNITY`, `HIGH` | Keyword category + `OPPORTUNITY→HIGH` |
| TC6 | Academic category + priority | contains `workshop`/`seminar`/`lecture` | `APPROVED`, `ACADEMIC`, `MEDIUM` | `ACADEMIC→MEDIUM` |
| TC7 | Social category | contains `club`/`society`/`social` | `APPROVED`, `SOCIAL`, `NORMAL` | `SOCIAL→NORMAL` |
| TC8 | Category precedence: opportunity > academic > social > general | contains both `internship` and `seminar` | `APPROVED`, `OPPORTUNITY`, `HIGH` | `OPPORTUNITY` takes precedence over `ACADEMIC` |

Notes:

- Keyword groups are fixed by the project PDF:
  - OPPORTUNITY: `career`, `internship`, `recruitment`
  - ACADEMIC: `workshop`, `seminar`, `lecture`
  - SOCIAL: `club`, `society`, `social`

## Case Files

Inputs and expected outputs are stored in `tests/cases/`:

- `tc1_incomplete_missing_field.json`
- `tc2_invalid_date.json`
- `tc3_short_description.json`
- `tc4_general_approved.json`
- `tc5_opportunity.json`
- `tc6_academic.json`
- `tc7_social.json`
- `tc8_precedence.json`

