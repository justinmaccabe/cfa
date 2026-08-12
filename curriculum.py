"""The CFA Level II curriculum, as static reference data.

This is the backbone the whole tracker hangs off: the 45 official 2026/2027
learning modules, grouped by topic, with the Schweser book each one lives in and
the CFA Institute topic-weight ranges. db.py seeds the `modules` table from here
on first run, so editing a name/weight here and re-seeding a fresh DB keeps a
single source of truth.

STUDY_ORDER is *our* planned topic sequence, not the curriculum's print order.
It reflects the plan we set from Justin's L1 results: Quant pulled to the front
(his one persistent soft spot, and the regression machinery is reused in PM/FSA/
Econ), the big valuation topics next while energy is high, Ethics run in parallel
throughout rather than blocked anywhere. It's advisory — the schedule authority
is still the xlsx planner; this just orders the Curriculum view sensibly.
"""

# Topic -> (weight_low %, weight_high %). CFA Institute L2 published ranges;
# unchanged for 2027 (only Ethics *content* was restructured, not its weight).
TOPIC_WEIGHTS = {
    "Ethics":               (10, 15),
    "Quantitative Methods": (5, 10),
    "Economics":            (5, 10),
    "Financial Statement Analysis": (10, 15),
    "Corporate Issuers":    (5, 10),
    "Equity Investments":   (10, 15),
    "Fixed Income":         (10, 15),
    "Derivatives":          (5, 10),
    "Alternative Investments": (5, 10),
    "Portfolio Management": (10, 15),
}

# Our planned study sequence (1 = first). Ethics = 99 => "parallel, all the way
# through," not a block you sit down and do once.
STUDY_ORDER = {
    "Quantitative Methods": 1,
    "Equity Investments":   2,
    "Fixed Income":         3,
    "Financial Statement Analysis": 4,
    "Portfolio Management": 5,
    "Derivatives":          6,
    "Corporate Issuers":    7,
    "Economics":            8,
    "Alternative Investments": 9,
    "Ethics":               99,
}

# From Justin's L1 score reports (Aug 2025 fail, May 2026 pass). Relative to the
# candidate average on each attempt: below / at / above. Drives the "watch list"
# highlighting in the app so weak-at-L1 topics stay visible.
L1_SIGNAL = {
    "Quantitative Methods": "below",   # below both times; lowest on the pass (~45%)
    "Equity Investments":   "at",      # stuck ~average both times
    "Ethics":               "at",      # middling both times; L2 swing factor
    "Economics":            "above",
    "Financial Statement Analysis": "above",
    "Corporate Issuers":    "above",
    "Fixed Income":         "above",
    "Derivatives":          "above",   # consistent strength
    "Alternative Investments": "at",
    "Portfolio Management": "above",   # huge turnaround Aug->May
}

# (topic, module name, schweser_book, schweser_reading_no) in curriculum order.
MODULES = [
    # ---- Book 1: Quantitative Methods (R1-4) + Economics (R5-6) -------------
    ("Quantitative Methods", "Basics of Multiple Regression and Underlying Assumptions", 1, 1),
    ("Quantitative Methods", "Evaluating Regression Model Fit and Interpreting Model Results", 1, 1),
    ("Quantitative Methods", "Model Misspecification", 1, 1),
    ("Quantitative Methods", "Extensions of Multiple Regression", 1, 1),
    ("Quantitative Methods", "Time-Series Analysis", 1, 2),
    ("Quantitative Methods", "Machine Learning", 1, 3),
    ("Quantitative Methods", "Big Data Projects", 1, 4),
    ("Economics", "Currency Exchange Rates: Understanding Equilibrium Value", 1, 5),
    ("Economics", "Economic Growth", 1, 6),
    # ---- Book 2: FSA (R7-12) + Corporate Issuers (R13-16) ------------------
    ("Financial Statement Analysis", "Intercorporate Investments", 2, 7),
    ("Financial Statement Analysis", "Employee Compensation: Post-Employment and Share-Based", 2, 8),
    ("Financial Statement Analysis", "Multinational Operations", 2, 9),
    ("Financial Statement Analysis", "Analysis of Financial Institutions", 2, 10),
    ("Financial Statement Analysis", "Evaluating Quality of Financial Reports", 2, 11),
    ("Financial Statement Analysis", "Integration of Financial Statement Analysis Techniques", 2, 12),
    ("Corporate Issuers", "Analysis of Dividends and Share Repurchases", 2, 13),
    ("Corporate Issuers", "ESG Considerations in Investment Analysis", 2, 14),
    ("Corporate Issuers", "Cost of Capital: Advanced Topics", 2, 15),
    ("Corporate Issuers", "Corporate Restructuring", 2, 16),
    # ---- Book 3: Equity Investments (R17-22) -------------------------------
    ("Equity Investments", "Equity Valuation: Applications and Processes", 3, 17),
    ("Equity Investments", "Discounted Dividend Valuation", 3, 18),
    ("Equity Investments", "Free Cash Flow Valuation", 3, 19),
    ("Equity Investments", "Market-Based Valuation: Price and Enterprise Value Multiples", 3, 20),
    ("Equity Investments", "Residual Income Valuation", 3, 21),
    ("Equity Investments", "Private Company Valuation", 3, 22),
    # ---- Book 4: Fixed Income (R23-27) + Derivatives (R28-29) + Alts (R30-33)
    ("Fixed Income", "The Term Structure and Interest Rate Dynamics", 4, 23),
    ("Fixed Income", "The Arbitrage-Free Valuation Framework", 4, 24),
    ("Fixed Income", "Valuation and Analysis of Bonds with Embedded Options", 4, 25),
    ("Fixed Income", "Credit Analysis Models", 4, 26),
    ("Fixed Income", "Credit Default Swaps", 4, 27),
    ("Derivatives", "Pricing and Valuation of Forward Commitments", 4, 28),
    ("Derivatives", "Valuation of Contingent Claims", 4, 29),
    ("Alternative Investments", "Introduction to Commodities and Commodity Derivatives", 4, 30),
    ("Alternative Investments", "Overview of Types of Real Estate Investment", 4, 31),
    ("Alternative Investments", "Investments in Real Estate through Publicly Traded Securities", 4, 32),
    ("Alternative Investments", "Hedge Fund Strategies", 4, 33),
    # ---- Book 5: Portfolio Management (R34-39) + Ethics (R40-42) -----------
    # Ethics note: the official 2027 outline splits "Guidance for Standards" into seven
    # LMs, one per Standard I-VII, where Schweser (and so R41 below) keeps one reading
    # with items 41.1-41.10. The LOS checklist surfaces the official per-Standard
    # grouping inside R41, so nothing is lost by leaving the reading whole.
    ("Portfolio Management", "Economics and Investment Markets", 5, 34),
    ("Portfolio Management", "Analysis of Active Portfolio Management", 5, 35),
    ("Portfolio Management", "Exchange-Traded Funds: Mechanics and Applications", 5, 36),
    ("Portfolio Management", "Using Multifactor Models", 5, 37),
    ("Portfolio Management", "Measuring and Managing Market Risk", 5, 38),
    ("Portfolio Management", "Backtesting and Simulation", 5, 39),
    ("Ethics", "Code of Ethics and Standards of Professional Conduct", 5, 40),
    ("Ethics", "Guidance for Standards I-VII", 5, 41),
    ("Ethics", "Application of the Code and Standards: Level II", 5, 42),
]

# Spaced-retrieval review lags (days after completion). Mirrors the xlsx planner's
# +3 / +14 / +45 schedule, which is grounded in the expanding-interval literature
# (Cepeda 2006; Roediger & Karpicke 2006). Review = practice questions from memory,
# NOT a re-read.
REVIEW_LAGS = (3, 14, 45)

TOPICS = list(TOPIC_WEIGHTS.keys())

# Sub-reading workflow states (the Status dropdown). COMPLETE_STATES are the ones
# that count as "content done" for section roll-up and realized-progress, and that
# arm the spaced-review clock.
STATUS_OPTIONS = [
    "Not Started", "Reading in Process", "Reading Completed",
    "Practice in Process", "Practice Complete", "Pending Review", "Reviewed",
]
COMPLETE_STATES = {"Practice Complete", "Pending Review", "Reviewed"}
# a module counts as "read" (fills the Curriculum bar) once it hits Reading Completed+
READ_DONE_STATES = {"Reading Completed", "Practice in Process", "Practice Complete"}

# One-time curated formula backfill (item code -> multi-line text). Applied once via a
# settings flag, so it never overwrites or re-adds after you edit/clear it.
FORMULA_SEED = {
    "1.2": ("R² = (Total Var − Unexplained Var) / Total Var = SSR/SST = 1 − SSE/SST\n"
            "Adjusted R² = 1 − [(n−1)/(n−k−1)] × (1 − R²)\n"
            "AIC = n·ln(SSE/n) + 2(k+1)   (lower = better; favors prediction)\n"
            "BIC = n·ln(SSE/n) + ln(n)·(k+1)   (lower = better; penalizes complexity more)\n"
            "Partial F = [(SSE_R − SSE_U)/q] / [SSE_U/(n−k−1)]   (q = # restrictions)\n"
            "Overall F = MSR/MSE = (RSS/k) / (SSE/(n−k−1))"),
}
# Actively being worked (still shows on the agenda). Practice-Complete and beyond
# drop off and only reappear through the review queue when a review is actually due.
ACTIVE_STATES = {"Reading in Process", "Reading Completed", "Practice in Process"}


# Schweser study sub-modules (171 total): (section_id, code, title).
# section_id is the 1-based index into MODULES above. Extracted from the Schweser
# TOCs; the granular checklist + spaced reviews run at this level (~684 touchpoints),
# while the Calendar stays at the coarser 45-section level.
SUBMODULES = [
    (1, '1.1', "Basics of Multiple Regression and Underlying Assumptions"),
    (2, '1.2', "Evaluating Regression Model Fit and Interpreting Model Results"),
    (3, '1.3', "Model Specification"),
    (4, '1.4', "Extensions of Multiple Regression"),
    (5, '2.1', "Linear and Log-Linear Trend Models"),
    (5, '2.2', "Autoregressive (AR) Models"),
    (5, '2.3', "Random Walks and Unit Roots"),
    (5, '2.4', "Seasonality"),
    (5, '2.5', "ARCH and Multiple Time Series"),
    (6, '3.1', "Types of Learning and Overfitting Problems"),
    (6, '3.2', "Supervised Learning Algorithms"),
    (6, '3.3', "Unsupervised Learning Algorithms and Other Models"),
    (7, '4.1', "Data Analysis Steps"),
    (7, '4.2', "Data Exploration"),
    (7, '4.3', "Model Training and Evaluation"),
    (8, '5.1', "Forex Quotes, Spreads, and Triangular Arbitrage"),
    (8, '5.2', "Mark-to-Market Value, and Parity Conditions"),
    (8, '5.3', "Exchange Rate Determinants, Carry Trade, and Central Bank Influence"),
    (9, '6.1', "Growth Factors and Production Function"),
    (9, '6.2', "Growth Accounting and Influencing Factors"),
    (9, '6.3', "Growth and Convergence Theories"),
    (10, '7.1', "Classifications"),
    (10, '7.2', "Investments in Financial Assets (IFRS 9)"),
    (10, '7.3', "Investment in Associates, Part 1—Equity Method"),
    (10, '7.4', "Investment in Associates, Part 2"),
    (10, '7.5', "Business Combinations: Balance Sheet"),
    (10, '7.6', "Business Combinations: Income Statement"),
    (10, '7.7', "Business Combinations: Goodwill"),
    (10, '7.8', "Joint Ventures"),
    (10, '7.9', "Special Purpose Entities"),
    (11, '8.1', "Share-Based Compensation"),
    (11, '8.2', "Post-Employment Benefits"),
    (12, '9.1', "Transaction Exposure"),
    (12, '9.2', "Translation"),
    (12, '9.3', "Temporal Method"),
    (12, '9.4', "Current Rate Method"),
    (12, '9.5', "Example"),
    (12, '9.6', "Ratios"),
    (12, '9.7', "Hyperinflation"),
    (12, '9.8', "Tax, Sales Growth, Financial Results"),
    (13, '10.1', "Financial Institutions"),
    (13, '10.2', "Capital Adequacy and Asset Quality"),
    (13, '10.3', "Management Capabilities and Earnings Quality"),
    (13, '10.4', "Liquidity Position and Sensitivity to Market Risk"),
    (13, '10.5', "Other Factors"),
    (13, '10.6', "Insurance Companies"),
    (14, '11.1', "Quality of Financial Reports"),
    (14, '11.2', "Evaluating Earnings Quality, Part 1"),
    (14, '11.3', "Evaluating Earnings Quality, Part 2"),
    (14, '11.4', "Evaluating Cash Flow Quality"),
    (14, '11.5', "Evaluating Balance Sheet Quality"),
    (15, '12.1', "Framework for Analysis"),
    (15, '12.2', "Earnings Sources and Performance"),
    (15, '12.3', "Asset Base and Capital Structure"),
    (15, '12.4', "Capital Allocation"),
    (15, '12.5', "Earnings Quality and Cash Flow Analysis"),
    (15, '12.6', "Market Value Decomposition"),
    (16, '13.1', "Theories of Dividend Policy"),
    (16, '13.2', "Stock Buybacks"),
    (17, '14.1', "Global Variations in Ownership Structures"),
    (17, '14.2', "Evaluating ESG Exposures"),
    (18, '15.1', "Factors Affecting the Cost of Capital and the Cost of Debt"),
    (18, '15.2', "ERP and the Cost of Equity"),
    (19, '16.1', "Restructuring Types and Motivations"),
    (19, '16.2', "Valuation"),
    (19, '16.3', "Evaluation"),
    (20, '17.1', "Equity Valuation: Applications and Processes"),
    (21, '18.1', "DDM Basics"),
    (21, '18.2', "Gordon Growth Model"),
    (21, '18.3', "Multiperiod Models"),
    (22, '19.1', "FCF Computation"),
    (22, '19.2', "Fixed CAPITAL and Working Capital"),
    (22, '19.3', "Variations of Formulae"),
    (22, '19.4', "Example"),
    (22, '19.5', "FCF Other Aspects"),
    (23, '20.1', "P/E Multiple"),
    (23, '20.2', "P/B Multiple"),
    (23, '20.3', "P/S and P/CF Multiple"),
    (23, '20.4', "EV and Other Aspects"),
    (24, '21.1', "Residual Income Defined"),
    (24, '21.2', "Residual Income Computation"),
    (24, '21.3', "Constant Growth Model for RI"),
    (24, '21.4', "Continuing Residual Income"),
    (24, '21.5', "Strengths/Weaknesses"),
    (25, '22.1', "Private Company Basics"),
    (25, '22.2', "Discount Rate"),
    (25, '22.3', "Valuation"),
    (26, '23.1', "Spot and Forward Rates, Part 1"),
    (26, '23.2', "Spot and Forward Rates, Part 2"),
    (26, '23.3', "The Swap Rate Curve"),
    (26, '23.4', "Spread Measures"),
    (26, '23.5', "Term Structure Theory"),
    (26, '23.6', "Yield Curve Risks and Economic Factors"),
    (27, '24.1', "Binomial Trees, Part 1"),
    (27, '24.2', "Binomial Trees, Part 2"),
    (27, '24.3', "Interest Rate Models"),
    (28, '25.1', "Types of Embedded Options"),
    (28, '25.2', "Valuing Bonds With Embedded Options, Part 1"),
    (28, '25.3', "Valuing Bonds With Embedded Options, Part 2"),
    (28, '25.4', "Option-Adjusted Spread"),
    (28, '25.5', "Duration"),
    (28, '25.6', "Key Rate Duration"),
    (28, '25.7', "Capped and Floored Floaters"),
    (28, '25.8', "Convertible Bonds"),
    (29, '26.1', "Credit Risk Measures"),
    (29, '26.2', "Analysis of Credit Risk"),
    (29, '26.3', "Credit Scores and Credit Ratings"),
    (29, '26.4', "Structural and Reduced Form Models"),
    (29, '26.5', "Credit Spread Analysis"),
    (29, '26.6', "Credit Spread"),
    (29, '26.7', "Credit Analysis of Securitized Debt"),
    (30, '27.1', "CDS Features and Terms"),
    (30, '27.2', "Factors Affecting CDS Pricing"),
    (30, '27.3', "CDS Usage"),
    (31, '28.1', "Pricing and Valuation Concepts"),
    (31, '28.2', "Pricing and Valuation of Equity Forwards"),
    (31, '28.3', "Pricing and Valuation of Fixed Income Forwards"),
    (31, '28.4', "Pricing and Valuation of Forward Rate Agreements"),
    (31, '28.5', "Pricing and Valuation of Interest Rate Swaps"),
    (31, '28.6', "Currency Swaps"),
    (31, '28.7', "Equity Swaps"),
    (32, '29.1', "The Binomial Model"),
    (32, '29.2', "Two Period Binomial Model and Put-Call Parity"),
    (32, '29.3', "American Options"),
    (32, '29.4', "Hedge Ratio"),
    (32, '29.5', "Interest Rate Options"),
    (32, '29.6', "Black-Scholes-Merton and Swaptions"),
    (32, '29.7', "Option Greeks and Dynamic Hedging"),
    (33, '30.1', "Introduction and Theories of Return"),
    (33, '30.2', "Analyzing Returns and Index Construction"),
    (34, '31.1', "Real Estate Features"),
    (34, '31.2', "Value Drivers and Property Types"),
    (34, '31.3', "Due Diligence, Valuation, and Indexes"),
    (35, '32.1', "Investments in Real Estate Through Publicly Traded Securities"),
    (36, '33.1', "Overview of Hedge Fund Strategies"),
    (36, '33.2', "Equity, Event-Driven, and Relative Value Strategies"),
    (36, '33.3', "Opportunistic, Specialist, and Multi-Manager Strategies"),
    (36, '33.4', "Factor Models and Portfolio Impact of Hedge Funds"),
    (37, '34.1', "Valuation and Interest Rates"),
    (37, '34.2', "The Business Cycle"),
    (38, '35.1', "Value Added by Active Management"),
    (38, '35.2', "The Information Ratio vs. the Sharpe Ratio"),
    (38, '35.3', "The Fundamental Law"),
    (38, '35.4', "Active Management"),
    (39, '36.1', "ETF Mechanics and Tracking Error"),
    (39, '36.2', "Spreads, Pricing Relative to NAV, and Costs"),
    (39, '36.3', "ETF Risks and Portfolio Applications"),
    (40, '37.1', "Multifactor Models"),
    (40, '37.2', "Macroeconomic Factor Models, Fundamental Factor Models, and Statistical Factor Models"),
    (40, '37.3', "Multifactor Model Risk and Return"),
    (41, '38.1', "Value at Risk (VAR)"),
    (41, '38.2', "Using VaR"),
    (41, '38.3', "Sensitivity and Scenario Risk Measures"),
    (41, '38.4', "Applications of Risk Measures"),
    (41, '38.5', "Constraints and Capital Allocation Decisions"),
    (42, '39.1', "Introduction to Backtesting"),
    (42, '39.2', "Backtesting an Investment Strategy"),
    (42, '39.3', "Metrics, Visuals, and Problems in Backtesting"),
    (42, '39.4', "Scenario Analysis and Sensitivity Analysis"),
    (43, '40.1', "Introduction to the Code and Standards"),
    (44, '41.1', "Standards I(A) and I(B)"),
    (44, '41.2', "Standards I(C), I(D), AND I(E)"),
    (44, '41.3', "Standards II(A) and II(B)"),
    (44, '41.4', "Standard III(A)"),
    (44, '41.5', "Standards III(B) and III(C)"),
    (44, '41.6', "Standards III(D) and III(E)"),
    (44, '41.7', "Standards IV(A), IV(B), and IV(C)"),
    (44, '41.8', "Standard V"),
    (44, '41.9', "Standard VI"),
    (44, '41.10', "Standard VII"),
    (45, '42.1', "Ethics Case Studies"),
]


# ---- Reading-level structure (the app's "sections" = Schweser readings) --------
# Collapse the 45 LMs into 42 readings; reading 1's four LMs become "Multiple
# Regression". Each reading holds its X.Y modules + Key Concepts + Module Quiz.
READING_TITLE_OVERRIDE = {1: "Multiple Regression"}
READINGS = []            # (topic, title, book, reading_no)
_seen_rd = set()
for _t, _n, _bk, _rd in MODULES:
    if _rd in _seen_rd:
        continue
    _seen_rd.add(_rd)
    READINGS.append((_t, READING_TITLE_OVERRIDE.get(_rd, _n), _bk, _rd))

_mods_by_reading = {}
for _sid, _code, _title in SUBMODULES:
    _mods_by_reading.setdefault(int(_code.split(".")[0]), []).append((_code, _title))

ITEMS = []               # (reading_no, code, name) — modules, then Key Concepts, then Quiz
for _t, _title, _bk, _rd in READINGS:
    for _code, _mt in _mods_by_reading.get(_rd, []):
        ITEMS.append((_rd, _code, _mt))
    ITEMS.append((_rd, "", "Key Concepts"))
    ITEMS.append((_rd, "", "Module Quiz"))

# Item workflow states (reviews live at the READING level, so no review states here).
ITEM_STATUS_OPTIONS = ["Not Started", "Reading in Process", "Reading Completed",
                       "Practice in Process", "Practice Complete"]
ITEM_COMPLETE = {"Practice Complete"}

# ---- the per-reading study loop -------------------------------------------
# "Give each resource one job": MM teaches it, the CFA curriculum is the authority
# (and the questions that match the exam), Schweser is review/formulas. These are the
# five fixed steps to run on EVERY reading, tracked at the READING level rather than
# per item — one MM video covers a whole reading, so the X.Y tier is the wrong grain.
#
# Four are simple ticks. The fifth, CFA practice questions, is a done/total pair
# instead: it gets worked through over several sittings, and the total is typed by
# hand per reading (no CFAI parsing). It renders below these four because it needs
# the number pair, which is also why it isn't in this list.
STUDY_LOOP_FLAGS = [
    ("mm_video",     "MM video",      "Mark Meldrum video for this reading watched"),
    ("cfa_read",     "CFA read",      "Official CFA reading skimmed — the blue-box examples especially"),
    ("mm_q",         "MM Qs",         "Mark Meldrum practice questions done"),
    ("formula_done", "Formula sheet", "Formula sheet / Schweser QuickSheet updated for this reading"),
]
STUDY_LOOP_STEPS = len(STUDY_LOOP_FLAGS) + 1     # + CFA practice questions (done/total)
RESOURCE_ROLES = "MM = teacher · CFA = authority + Qs · Schweser = review / formulas"
