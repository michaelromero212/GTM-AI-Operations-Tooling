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
        ("REQ-001", "Sarah Chen", "AE", "Cloud consumption-based churn early warning system using real-time engagement signals.", "Expansion & Renewal", "CRITICAL", "IN BUILD", "2026-02-15 09:00:00"),
        ("REQ-002", "James Rodriguez", "Customer Success", "Automated QBR data aggregation from data streaming sources for enterprise customers.", "Onboarding & Adoption", "HIGH", "INTAKE", "2026-02-16 10:30:00"),
        ("REQ-003", "Priya Patel", "RevOps", "Real-time deal health scoring using activity signals and data motion patterns.", "Deal Execution", "MEDIUM", "INTAKE", "2026-02-16 11:45:00"),
        ("REQ-004", "Mike Ross", "SDR", "AI-powered personalized outreach agent for high-intent 'Cloud Pulse' signals.", "Pipeline Generation", "HIGH", "DEPLOYED", "2026-02-14 14:20:00"),
        ("REQ-005", "Elena Gomez", "Sales (Manager)", "Automated forecast risk detection based on deal velocity and data stream signals.", "Deal Execution", "CRITICAL", "SCOPING", "2026-02-17 08:30:00"),
        ("REQ-006", "David Kim", "Customer Success", "Automatic success plan generation based on platform usage bottlenecks.", "Onboarding & Adoption", "MEDIUM", "QA", "2026-02-17 10:15:00"),
        ("REQ-007", "Rachel Foster", "Sales (Manager)", "Territory 'Data in Motion' map for identifying real-time expansion pockets.", "Expansion & Renewal", "MEDIUM", "INTAKE", "2026-02-17 14:00:00"),
        ("REQ-008", "Alex Nguyen", "RevOps", "Automated CRM data hygiene scanning for cloud-native record attributes.", "Pipeline Generation", "LOW", "INTAKE", "2026-02-17 15:30:00")
    ]

    con.executemany("""
        INSERT INTO intake_requests (id, requester_name, requester_team, pain_point, gtm_stage, urgency, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, requests_data)

    # ── Backlog Items ──
    # Confluent-specific GTM stages
    STAGES = ["Pipeline Generation", "Deal Execution", "Onboarding & Adoption", "Expansion & Renewal"]
    TEAMS = ["Sales (SDR)", "Sales (AE)", "Customer Success", "RevOps", "Marketing Ops", "Sales (Manager)"]
    URGENCIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    STATUSES = ["INTAKE", "SCOPING", "IN BUILD", "QA", "DEPLOYED", "MEASURING"]

    backlog_data = [
        ("BLG-001", "REQ-001", "Cloud Churn Early Warning", "Sarah Chen", "AE", "Expansion & Renewal", "Strategic", "AI Agent", 9, "In Build", "Maya (Data Sci)", "10 hrs/week"),
        ("BLG-002", "REQ-002", "Automated QBR Generator", "James Rodriguez", "Customer Success", "Onboarding & Adoption", "Medium", "Workflow Automation", 8, "Intake", None, "12 hrs/week"),
        ("BLG-003", "REQ-003", "Real-time Deal Health Scorer", "Priya Patel", "RevOps", "Deal Execution", "Medium", "AI Agent", 7, "Intake", None, "8 hrs/week"),
        ("BLG-004", "REQ-004", "Cloud Pulse Outreach Agent", "Mike Ross", "SDR", "Pipeline Generation", "Quick Win", "AI Agent", 8, "Deployed", "Alex (AI Eng)", "15 hrs/week"),
        ("BLG-005", "REQ-005", "Forecast Risk Detector", "Elena Gomez", "Sales (Manager)", "Deal Execution", "Strategic", "AI Agent", 9, "Scoping", "Maya (Data Sci)", "10 hrs/week"),
        ("BLG-006", "REQ-006", "Auto Success Plan Generator", "David Kim", "Customer Success", "Onboarding & Adoption", "Medium", "AI Agent", 7, "QA", "Alex (AI Eng)", "7 hrs/week"),
        ("BLG-007", "REQ-007", "Territory Data in Motion Map", "Rachel Foster", "Sales (Manager)", "Expansion & Renewal", "Medium", "Workflow Automation", 6, "Intake", None, "6 hrs/week"),
        ("BLG-008", "REQ-008", "CRM Cloud Data Hygiene", "Alex Nguyen", "RevOps", "Pipeline Generation", "Quick Win", "Data Fix", 5, "Intake", None, "5 hrs/week"),
    ]

    con.executemany("""
        INSERT INTO backlog_items (id, request_id, title, requester_name, requester_team, gtm_stage, complexity, approach, priority_score, status, assigned_to, estimated_time_savings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, backlog_data)

    # ── Impact Metrics (for deployed items) ──
    # Historical ROI Data for Impact Tracker
    roi_data = [
        ("IMP-001", "REQ-004", "Cloud Pulse Outreach Agent", "DEPLOYED", 20.0, 4.0, 0.88, 11000.0, 2),
        ("IMP-002", "REQ-001", "Cloud Churn Early Warning", "MEASURING", 15.0, 3.0, 0.78, 8500.0, 3),
        ("IMP-003", "REQ-006", "Auto Success Plan Generator", "QA", 22.0, 5.0, 0.0, 0.0, 0),
    ]

    con.executemany("""
        INSERT INTO impact_metrics (id, request_id, title, status, manual_time_before, ai_time_after, adoption_rate, roi_estimate, weeks_deployed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, roi_data)

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

