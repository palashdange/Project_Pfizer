"""Central policy values for the Project Sankalp pilot.

Page references identify the printed page ("Page N of 6") in CO-POL-014 v4.2,
data-pack/02_trade_terms_and_returns_policy.pdf. All pages verified 25 Nov 2026.
"""

# Minimum residual shelf life at invoice time, expressed as a percentage.
MIN_REMAINING_SHELF_LIFE_PCT = 60.0  # CO-POL-014 v4.2 §7.1 p.4

# Absolute residual shelf-life lower bound, in addition to the percentage rule.
MIN_REMAINING_SHELF_LIFE_DAYS = 60  # CO-POL-014 v4.2 §7.1 p.4

# Claim filing window on either side of the official batch expiry date.
EXPIRY_CLAIM_WINDOW_DAYS = 90  # CO-POL-014 v4.2 §5.2 p.3

# Filing limit for breakage-in-transit and short-supply claims after invoice.
BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS = 7  # CO-POL-014 v4.2 §5.2 p.3

# Target period to approve and raise a claim credit note.
CREDIT_NOTE_SLA_DAYS = 30  # CO-POL-014 v4.2 §5.6 p.4

# Free-of-charge goods cap as a share of eligible invoiced value.
FOC_CAP_PCT = 3.0  # CO-POL-014 v4.2 §4.4 p.2

# Time allowed for CFA verification, expressed in working days.
CFA_VERIFICATION_WINDOW_WORKING_DAYS = 10  # CO-POL-014 v4.2 §5.6 p.4

# Model call limits. A PILOT DESIGN CHOICE, not a policy number: a review normally answers in 2-3 s,
# so 20 s means the provider is stuck. One retry covers a dropped connection; after that the graph's
# existing failure path takes over (parse -> NEEDS_PERSON, explain -> code fallback text).
MODEL_TIMEOUT_SECONDS = 20
MODEL_MAX_RETRIES = 1

# Near-repeat claim screen. A PILOT DESIGN CHOICE, not a CO-POL-014 number: §5.6 p.4 only says to
# check for an earlier claim on the same stockist and batch. Chosen from the register: 17 claims sit
# within 1% or 1 pack of an earlier claim on the same stockist/batch before the spread widens.
DUPLICATE_NEAR_QTY_TOLERANCE_PCT = 1.0
DUPLICATE_NEAR_QTY_MIN_PACKS = 1

# Quarter-end scheme register, CO-POL-014 v4.2 Annexure B pp.5-6. Each circular is valid from the
# 22nd of the quarter's last month to that month's last day; the minimum order is 1.5 times the
# stockist's average monthly purchase of the SKU over the previous three months (Annexure B p.5).
SCHEME_VALID_FROM_DAY = 22  # Annexure B p.5
SCHEME_MIN_ORDER_MULTIPLE = 1.5  # Annexure B p.5
SCHEME_LOOKBACK_MONTHS = 3  # Annexure B p.5
SCHEME_TIER_A_SKUS = (
    "PFL1001", "PFL1002", "PFL1003", "PFL1101", "PFL1102",
    "PFL1103", "PFL1105", "PFL1202", "PFL1301", "PFL1303",
)  # SC/24/06, Annexure B p.5
SCHEME_TIER_B_SKUS = ("PFL1004", "PFL1104", "PFL1201", "PFL1302", "PFL1401")  # SC/24/12, Annexure B p.5
# Free packs per 10 invoiced, by scheme code: Tier A 10+1 to FY25 Q2, 10+2 from FY25 Q3; Tier B 10+1.
SCHEME_REGISTER = {
    "QS-FY25Q1-A": ("SC/24/06", 1), "QS-FY25Q2-A": ("SC/24/09", 1),
    "QS-FY25Q3-A": ("SC/24/12", 2), "QS-FY25Q3-B": ("SC/24/12", 1),
    "QS-FY25Q4-A": ("SC/25/03", 2), "QS-FY25Q4-B": ("SC/25/03", 1),
    "QS-FY26Q1-A": ("SC/25/06", 2), "QS-FY26Q1-B": ("SC/25/06", 1),
    "QS-FY26Q2-A": ("SC/25/09", 2), "QS-FY26Q2-B": ("SC/25/09", 1),
    "QS-FY26Q3-A": ("SC/25/12", 2), "QS-FY26Q3-B": ("SC/25/12", 1),
    "QS-FY26Q4-A": ("SC/26/03", 2), "QS-FY26Q4-B": ("SC/26/03", 1),
    "QS-FY27Q1-A": ("SC/26/06", 2), "QS-FY27Q1-B": ("SC/26/06", 1),
    "QS-FY27Q2-A": ("SC/26/09", 2), "QS-FY27Q2-B": ("SC/26/09", 1),
}  # Annexure B pp.5-6

# C&F stock norms (C&F agreement SC-AGR-CF-003). Each C&F is topped up monthly to 2 months of its
# allocated volume (Schedule 2 §2.2 p.3) and must pick first-expiry-first-out (clause 6.3 p.2;
# Schedule 2 §2.3 p.3). A WMS change needs 30 days' notice and a batch-rule check (clause 4.3 p.2).
CFA_TOPUP_MONTHS = 2.0  # Schedule 2 §2.2 p.3
# FEFO signal: a PILOT THRESHOLD, not a contract number. A C&F is flagged when its share of dispatch
# lines that skipped an older on-hand batch is at least this multiple of the other C&Fs' median.
FEFO_SIGNAL_MULTIPLE = 2.0
# Average days in a month, to turn an outward rate per month into days.
DAYS_PER_MONTH = 30.4375

# Clause labels shared by the graph's rule checks and their audit evidence.
TRANSIT_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.2"
EXPIRY_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.2"
INVOICE_REFERENCE_POLICY_CLAUSE = "CO-POL-014 §5.4"
CLAIM_QUANTITY_POLICY_CLAUSE = "CO-POL-014 §5.5"
DUPLICATE_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.6"
CLAIM_VALUE_POLICY_CLAUSE = "CO-POL-014 §5.7"
BATCH_EXPIRY_POLICY_CLAUSE = "CO-POL-014 §5.2"
PASTED_FIELDS_POLICY_CLAUSE = "CO-POL-014 §5.3; §5.7"
SCHEME_CAP_POLICY_CLAUSE = "CO-POL-014 §4.4"
SCHEME_TERMS_POLICY_CLAUSE = "CO-POL-014 §4.2; Annexure B"
SCHEME_STOCK_NORM_POLICY_CLAUSE = "CO-POL-014 §4.5"
STOCK_EXPIRY_POLICY_CLAUSE = "CO-POL-014 §7.1-7.2"
STOCK_COVER_POLICY_CLAUSE = "C&F agreement Schedule 2 §2.2"
STOCK_FEFO_POLICY_CLAUSE = "C&F agreement clause 6.3, 4.3"
