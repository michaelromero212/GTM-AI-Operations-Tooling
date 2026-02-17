"""
Database seed script — populates DuckDB with realistic GTM operations data.
Run standalone: python -m data.seed
Or imported by the webapp on first launch.
"""
import duckdb
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "ops_hub.duckdb")


def get_connection(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Get a DuckDB connection (creates file if needed)."""
    return duckdb.connect(db_path)


def create_tables(con: duckdb.DuckDBPyConnection):
    """Create all tables if they don't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS intake_requests (
            id VARCHAR PRIMARY KEY,
            requester_name VARCHAR,
            requester_team VARCHAR,
            pain_point TEXT,
            workflow_stage VARCHAR,
            manual_time_hours DOUBLE,
            urgency VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gtm_stage VARCHAR,
            complexity VARCHAR,
            approach VARCHAR,
            priority_score INTEGER,
            triage_summary TEXT,
            requirements_json TEXT,
            status VARCHAR DEFAULT 'Intake'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS backlog_items (
            id VARCHAR PRIMARY KEY,
            request_id VARCHAR REFERENCES intake_requests(id),
            title VARCHAR,
            requester_name VARCHAR,
            requester_team VARCHAR,
            gtm_stage VARCHAR,
            complexity VARCHAR,
            approach VARCHAR,
            priority_score INTEGER,
            status VARCHAR DEFAULT 'Intake',
            assigned_to VARCHAR,
            estimated_time_savings VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id VARCHAR PRIMARY KEY,
            request_id VARCHAR REFERENCES intake_requests(id),
            version INTEGER,
            prompt_text TEXT,
            response_text TEXT,
            quality_score DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS impact_metrics (
            id VARCHAR PRIMARY KEY,
            request_id VARCHAR REFERENCES intake_requests(id),
            title VARCHAR,
            status VARCHAR,
            manual_time_before DOUBLE,
            ai_time_after DOUBLE,
            adoption_rate DOUBLE,
            roi_estimate DOUBLE,
            weeks_deployed INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type VARCHAR,
            actor VARCHAR,
            request_id VARCHAR,
            description TEXT,
            input_snapshot TEXT,
            output_snapshot TEXT
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS qa_checks (
            id VARCHAR PRIMARY KEY,
            request_id VARCHAR,
            workflow_title VARCHAR,
            check_name VARCHAR,
            status VARCHAR,
            details TEXT,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def seed_data(con: duckdb.DuckDBPyConnection):
    """Insert realistic seed data."""
    # Check if already seeded
    count = con.execute("SELECT COUNT(*) FROM intake_requests").fetchone()[0]
    if count > 0:
        return  # Already seeded

    # ── Intake Requests ──
    requests_data = [
        ("REQ-001", "Sarah Chen", "Sales (SDR)", "Our SDRs spend 30 min per lead researching company info, recent news, and tech stack before outreach. This is killing our daily lead capacity.", "Prospecting", 15.0, "High", "Pipeline Generation", "Medium", "AI Agent", 8, "Automate lead research aggregation to reduce SDR prep time"),
        ("REQ-002", "James Rodriguez", "Customer Success", "CSMs manually track renewal risk in spreadsheets. We have no early warning system — we find out accounts are churning when it's too late.", "Renewal Tracking", 10.0, "Critical", "Renewal & Expansion", "Strategic", "AI Agent", 9, "Build predictive churn early-warning system using engagement signals"),
        ("REQ-003", "Priya Patel", "RevOps", "Deal data in Salesforce is inconsistent — missing fields, wrong stages, duplicate contacts. We spend hours weekly on manual cleanup.", "Data Management", 8.0, "Medium", "Deal Execution", "Quick Win", "Data Fix", 6, "Automated data hygiene scanning and correction for CRM records"),
        ("REQ-004", "Marcus Thompson", "Sales (AE)", "After every customer meeting, I spend 20 min writing follow-up emails. Could AI draft these from my meeting notes?", "Follow-up", 5.0, "Medium", "Deal Execution", "Quick Win", "AI Agent", 7, "AI-generated follow-up emails from meeting notes and CRM context"),
        ("REQ-005", "Lisa Wang", "Marketing Ops", "We can't tell which campaigns are actually driving pipeline vs. just generating MQLs that never convert. Attribution is manual and unreliable.", "Campaign Attribution", 12.0, "High", "Pipeline Generation", "Strategic", "Workflow Automation", 8, "Automated multi-touch attribution connecting marketing campaigns to closed revenue"),
        ("REQ-006", "David Kim", "Customer Success", "Onboarding new customers takes 6 weeks because CSMs manually create and track implementation checklists. Every customer gets a slightly different experience.", "Onboarding", 20.0, "High", "Onboarding & Adoption", "Medium", "Workflow Automation", 7, "Standardized automated onboarding workflow with milestone tracking"),
        ("REQ-007", "Rachel Foster", "Sales (Manager)", "I can't get a real-time view of deal health across my team. I rely on reps self-reporting in stand-ups, which is always outdated.", "Pipeline Review", 6.0, "Medium", "Deal Execution", "Medium", "AI Agent", 6, "AI-powered deal health scoring using engagement and activity signals"),
        ("REQ-008", "Alex Nguyen", "RevOps", "Quarterly business reviews take 2 weeks to prepare because we're pulling data from 5 different systems and manually building slides.", "Reporting", 16.0, "Low", "Renewal & Expansion", "Medium", "Workflow Automation", 5, "Automated QBR data aggregation and narrative generation"),
    ]

    con.executemany("""
        INSERT INTO intake_requests (id, requester_name, requester_team, pain_point, workflow_stage, manual_time_hours, urgency, gtm_stage, complexity, approach, priority_score, triage_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, requests_data)

    # ── Backlog Items ──
    backlog_data = [
        ("BLG-001", "REQ-001", "AI Lead Research Assistant", "Sarah Chen", "Sales (SDR)", "Pipeline Generation", "Medium", "AI Agent", 8, "In Build", "Alex (AI Eng)", "12.5 hrs/week"),
        ("BLG-002", "REQ-002", "Churn Early Warning System", "James Rodriguez", "Customer Success", "Renewal & Expansion", "Strategic", "AI Agent", 9, "Scoping", "Maya (Data Sci)", "8 hrs/week"),
        ("BLG-003", "REQ-003", "CRM Data Hygiene Bot", "Priya Patel", "RevOps", "Deal Execution", "Quick Win", "Data Fix", 6, "Deployed", "Alex (AI Eng)", "6 hrs/week"),
        ("BLG-004", "REQ-004", "AI Follow-Up Drafter", "Marcus Thompson", "Sales (AE)", "Deal Execution", "Quick Win", "AI Agent", 7, "QA", "Alex (AI Eng)", "4 hrs/week"),
        ("BLG-005", "REQ-005", "Multi-Touch Attribution Engine", "Lisa Wang", "Marketing Ops", "Pipeline Generation", "Strategic", "Workflow Automation", 8, "Scoping", "Jordan (Ops)", "10 hrs/week"),
        ("BLG-006", "REQ-006", "Automated Onboarding Orchestrator", "David Kim", "Customer Success", "Onboarding & Adoption", "Medium", "Workflow Automation", 7, "In Build", "Jordan (Ops)", "15 hrs/week"),
        ("BLG-007", "REQ-007", "Deal Health AI Scorer", "Rachel Foster", "Sales (Manager)", "Deal Execution", "Medium", "AI Agent", 6, "Intake", None, "5 hrs/week"),
        ("BLG-008", "REQ-008", "QBR Auto-Generator", "Alex Nguyen", "RevOps", "Renewal & Expansion", "Medium", "Workflow Automation", 5, "Intake", None, "12 hrs/week"),
    ]

    con.executemany("""
        INSERT INTO backlog_items (id, request_id, title, requester_name, requester_team, gtm_stage, complexity, approach, priority_score, status, assigned_to, estimated_time_savings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, backlog_data)

    # ── Impact Metrics (for deployed items) ──
    impact_data = [
        ("IMP-001", "REQ-003", "CRM Data Hygiene Bot", "Deployed", 8.0, 1.5, 92.0, 4200.0, 6),
        ("IMP-002", "REQ-001", "AI Lead Research Assistant", "Measuring", 15.0, 3.0, 78.0, 8500.0, 3),
        ("IMP-003", "REQ-004", "AI Follow-Up Drafter", "QA", 5.0, 1.0, 0.0, 0.0, 0),
        ("IMP-004", "REQ-006", "Automated Onboarding Orchestrator", "In Build", 20.0, 5.0, 0.0, 0.0, 0),
    ]

    con.executemany("""
        INSERT INTO impact_metrics (id, request_id, title, status, manual_time_before, ai_time_after, adoption_rate, roi_estimate, weeks_deployed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, impact_data)

    # ── Prompt Versions ──
    prompt_data = [
        ("PV-001", "REQ-001", 1, "Research this lead and provide key talking points for an SDR.", "Company: Acme Corp, Industry: SaaS, Key Points: Series B funding, expanding to EMEA, uses AWS...", 6.5),
        ("PV-002", "REQ-001", 2, "You are an SDR research assistant. Given a lead's company name and industry, provide: 1) Company overview, 2) Recent news, 3) Tech stack signals, 4) Recommended talking points.", "**Acme Corp — SDR Research Brief**\n\n1. Overview: Mid-market SaaS...", 8.2),
        ("PV-003", "REQ-002", 1, "Analyze this customer's engagement data and predict churn risk.", "Based on the engagement signals, this account shows moderate risk...", 5.8),
        ("PV-004", "REQ-002", 2, "You are a customer health analyst. Given an account's engagement metrics (login frequency, support tickets, feature adoption, NPS), produce a risk score (1-10) and recommended actions.", "**Churn Risk Assessment**\n\nRisk Score: 7/10\nKey Signals: Login frequency down 40%...", 7.9),
    ]

    con.executemany("""
        INSERT INTO prompt_versions (id, request_id, version, prompt_text, response_text, quality_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, prompt_data)

    # ── Audit Log ──
    audit_data = [
        ("AUD-001", "2026-02-10 09:15:00", "triage", "System (AI)", "REQ-001", "AI triage completed for SDR lead research request — classified as Medium complexity, AI Agent approach", None, None),
        ("AUD-002", "2026-02-10 09:16:00", "intake_received", "Sarah Chen", "REQ-001", "New intake request submitted by Sales (SDR) team — 15 hrs/week manual effort reported", None, None),
        ("AUD-003", "2026-02-11 14:30:00", "triage", "System (AI)", "REQ-002", "AI triage completed for churn early-warning request — classified as Strategic complexity, AI Agent approach", None, None),
        ("AUD-004", "2026-02-12 10:00:00", "blueprint_generated", "System (AI)", "REQ-001", "Workflow blueprint auto-generated for AI Lead Research Assistant — 4 steps, 2 integrations", None, None),
        ("AUD-005", "2026-02-12 16:45:00", "prompt_tested", "Alex (AI Eng)", "REQ-001", "Prompt v2 tested in Prompt Lab — quality score improved from 6.5 to 8.2", "Research this lead...", "SDR Research Brief generated"),
        ("AUD-006", "2026-02-13 11:00:00", "qa_completed", "Alex (AI Eng)", "REQ-003", "QA checks passed for CRM Data Hygiene Bot — 4/4 checks passed, no PII exposure detected", None, None),
        ("AUD-007", "2026-02-13 14:20:00", "status_change", "Jordan (Ops)", "REQ-003", "CRM Data Hygiene Bot moved from QA → Deployed", None, None),
        ("AUD-008", "2026-02-14 09:00:00", "deployment", "Alex (AI Eng)", "REQ-003", "CRM Data Hygiene Bot deployed to production — rollout to RevOps team (12 users)", None, None),
        ("AUD-009", "2026-02-14 15:30:00", "prompt_tested", "Maya (Data Sci)", "REQ-002", "Prompt v2 tested for churn prediction — quality score improved from 5.8 to 7.9", None, None),
        ("AUD-010", "2026-02-15 10:15:00", "qa_completed", "Alex (AI Eng)", "REQ-004", "QA checks for AI Follow-Up Drafter — 3/4 passed, 1 warning (tone consistency)", None, None),
        ("AUD-011", "2026-02-16 08:45:00", "status_change", "Alex (AI Eng)", "REQ-001", "AI Lead Research Assistant moved from In Build → QA", None, None),
        ("AUD-012", "2026-02-17 09:00:00", "compliance_review", "Legal Review", "REQ-002", "Data usage compliance review initiated for churn model — customer engagement data requires DPA verification", None, None),
    ]

    con.executemany("""
        INSERT INTO audit_log (id, timestamp, event_type, actor, request_id, description, input_snapshot, output_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, audit_data)

    # ── QA Checks ──
    qa_data = [
        ("QA-001", "REQ-003", "CRM Data Hygiene Bot", "PII Detection", "pass", "No PII fields exposed in AI-generated outputs. Email and phone fields masked correctly.", "2026-02-13 10:30:00"),
        ("QA-002", "REQ-003", "CRM Data Hygiene Bot", "Hallucination Check", "pass", "Output field corrections validated against source CRM data — 98.5% accuracy.", "2026-02-13 10:32:00"),
        ("QA-003", "REQ-003", "CRM Data Hygiene Bot", "Prompt Injection", "pass", "Adversarial prompt inputs rejected correctly. No instruction override detected.", "2026-02-13 10:34:00"),
        ("QA-004", "REQ-003", "CRM Data Hygiene Bot", "Data Leakage", "pass", "Cross-account data isolation verified — no data bleed between tenant records.", "2026-02-13 10:36:00"),
        ("QA-005", "REQ-004", "AI Follow-Up Drafter", "PII Detection", "pass", "Customer names used appropriately. No SSN, financial, or health data in outputs.", "2026-02-15 10:00:00"),
        ("QA-006", "REQ-004", "AI Follow-Up Drafter", "Hallucination Check", "pass", "Follow-up content matches meeting notes context — no fabricated commitments.", "2026-02-15 10:02:00"),
        ("QA-007", "REQ-004", "AI Follow-Up Drafter", "Tone Consistency", "warning", "Tone slightly varies between formal and casual across generated drafts. Recommend adding style guide constraint.", "2026-02-15 10:04:00"),
        ("QA-008", "REQ-004", "AI Follow-Up Drafter", "Prompt Injection", "pass", "Adversarial inputs handled correctly. System prompt boundaries maintained.", "2026-02-15 10:06:00"),
        ("QA-009", "REQ-001", "AI Lead Research Assistant", "Bias Detection", "warning", "Minor geographic bias detected — US-based companies receive 15% more detail. Recommend balancing training examples.", "2026-02-16 14:00:00"),
        ("QA-010", "REQ-001", "AI Lead Research Assistant", "PII Detection", "pass", "Lead research outputs contain only company-level public data. No individual PII surfaced.", "2026-02-16 14:02:00"),
    ]

    con.executemany("""
        INSERT INTO qa_checks (id, request_id, workflow_title, check_name, status, details, run_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, qa_data)


def initialize_database(db_path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    """Create tables and seed data. Returns the connection."""
    con = get_connection(db_path)
    create_tables(con)
    seed_data(con)
    return con


if __name__ == "__main__":
    print("Initializing GTM AI Operations Hub database...")
    con = initialize_database()
    count = con.execute("SELECT COUNT(*) FROM intake_requests").fetchone()[0]
    audit_count = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    print(f"✅ Database ready — {count} intake requests, {audit_count} audit entries seeded")
    con.close()

