# Sample Documents

Auto-generated PDFs for exercising the signing tool end-to-end. None of these
are real documents — upload them through the app to test the workflow.

| File | Pages | Use for |
|---|---|---|
| `sample_partnership_addendum.pdf` | 1 | Basic happy-path: upload -> place -> confirm -> sign -> download |
| `sample_multi_page_agreement.pdf` | 3 | Page-selector correctness — confirm a signature placed on one page doesn't leak onto another |
| `sample_tri_partner_resolution.pdf` | 1 | Signing the same document multiple times, once per partner, and checking the audit log links all three events to the same document hash |
| `sample_capital_call_notice.pdf` | 1 | Off-center placement — signature line is on the right |
| `sample_landscape_cover_note.pdf` | 1 (landscape) | Non-portrait page size — confirm the overlay still lands on the line |
| `sample_us_letter_landscape.pdf` | 1 (US Letter landscape) | Non-A4 size (792 × 612 pt) — confirm size and orientation stay the same after signing |
| `sample_pack_01_ic_memo.pdf` | 4 | Sign last page only |
| `sample_pack_02_shareholders_agreement.pdf` | 6 | Longer A4 pack |
| `sample_pack_03_quarterly_report.pdf` | 5 (A4 landscape) | Convert landscape to portrait + letterhead |
| `sample_pack_04_side_letter.pdf` | 2 (Letter) | US Letter source |
| `sample_pack_05_legal_opinion.pdf` | 8 (Legal) | Tall Legal pages |
| `sample_pack_06_board_minutes.pdf` | 3 | Two signature lines on last page |
| `sample_pack_07_term_sheet.pdf` | 2 | Sign / initial every page |
| `sample_pack_08_kyc_pack.pdf` | 7 | Page jumping |
| `sample_pack_09_fund_iv_drawdown.pdf` | 3 | Fund 4 stamp + partner sign |
| `sample_pack_10_amc_policy.pdf` | 4 | AMC letterhead |
| `sample_pack_11_continuation_consent.pdf` | 5 (Letter) | Continuation Fund letterhead |
| `sample_pack_12_valuation_committee.pdf` | 4 (A4 landscape) | Landscape convert |
| `sample_pack_13_esop_approval.pdf` | 2 | Dual signatures |
| `sample_pack_14_audit_response.pdf` | 9 | Long convert |
| `sample_pack_15_a3_portfolio_map.pdf` | 2 (A3) | Oversize source down to A4 |
| `sample_pack_16_letterhead_stress.pdf` | 3 | Stamp every page with letterhead on |
| `sample_pack_17_mixed_signatories.pdf` | 4 | Sign pages 2 and 4 only |
| `sample_pack_18_fund2_closing.pdf` | 6 (Letter landscape) | Fund 2 letterhead |
| `sample_pack_19_angel_followon.pdf` | 3 | Fund 1 / Angel letterhead |
| `sample_pack_20_twelve_page_im.pdf` | 12 | Largest pack / navigation stress |

Regenerate with `python data/samples/generate.py` after editing the script.
