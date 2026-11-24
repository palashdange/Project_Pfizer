"""Central policy values for the Project Sankalp pilot.

Page references identify the printed page in CO-POL-014 v4.2. The supplied
PDF is a six-page file; pages for clauses beyond the user-cited §5.2 p.3 could
not be text-verified in this environment and should be confirmed before use.
"""

# Minimum residual shelf life at invoice time, expressed as a percentage.
MIN_REMAINING_SHELF_LIFE_PCT = 60.0  # CO-POL-014 v4.2 §7.1 p.5 (page to verify)

# Absolute residual shelf-life lower bound, in addition to the percentage rule.
MIN_REMAINING_SHELF_LIFE_DAYS = 60  # CO-POL-014 v4.2 §7.1 p.5 (page to verify)

# Claim filing window on either side of the official batch expiry date.
EXPIRY_CLAIM_WINDOW_DAYS = 90  # CO-POL-014 v4.2 §5.2 p.3

# Filing limit for breakage-in-transit and short-supply claims after invoice.
BREAKAGE_SHORT_SUPPLY_WINDOW_DAYS = 7  # CO-POL-014 v4.2 §5.2 p.3

# Target period to approve and raise a claim credit note.
CREDIT_NOTE_SLA_DAYS = 30  # CO-POL-014 v4.2 §5.6 p.4 (page to verify)

# Free-of-charge goods cap as a share of eligible invoiced value.
FOC_CAP_PCT = 3.0  # CO-POL-014 v4.2 §4.4 p.2 (page to verify)

# Time allowed for CFA verification, expressed in working days.
CFA_VERIFICATION_WINDOW_WORKING_DAYS = 10  # CO-POL-014 v4.2 §5.6 p.4 (page to verify)
