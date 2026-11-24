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

# Near-repeat claim screen. A PILOT DESIGN CHOICE, not a CO-POL-014 number: §5.6 p.4 only says to
# check for an earlier claim on the same stockist and batch. Chosen from the register: 17 claims sit
# within 1% or 1 pack of an earlier claim on the same stockist/batch before the spread widens.
DUPLICATE_NEAR_QTY_TOLERANCE_PCT = 1.0
DUPLICATE_NEAR_QTY_MIN_PACKS = 1

# Clause labels shared by the graph's rule checks and their audit evidence.
TRANSIT_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.2"
EXPIRY_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.2"
INVOICE_REFERENCE_POLICY_CLAUSE = "CO-POL-014 §5.4"
CLAIM_QUANTITY_POLICY_CLAUSE = "CO-POL-014 §5.5"
DUPLICATE_CLAIM_POLICY_CLAUSE = "CO-POL-014 §5.6"
CLAIM_VALUE_POLICY_CLAUSE = "CO-POL-014 §5.7"
BATCH_EXPIRY_POLICY_CLAUSE = "CO-POL-014 §5.2"
