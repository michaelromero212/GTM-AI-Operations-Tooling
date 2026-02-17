"""
Prompt templates for GTM AI Operations Hub
Each LLM task has a system prompt and a user prompt builder.
"""


# ─────────────────── INTAKE TRIAGE ───────────────────

TRIAGE_SYSTEM_PROMPT = """You are an AI operations analyst for a GTM (Go-To-Market) team.
Your job is to classify incoming automation requests from field teams.

For each request, you must output a JSON object with these fields:
- "gtm_stage": one of "Pipeline Generation", "Deal Execution", "Onboarding & Adoption", "Renewal & Expansion"
- "complexity": one of "Quick Win", "Medium", "Strategic"
- "approach": one of "AI Agent", "Workflow Automation", "Data Fix", "Process Change"
- "priority_score": integer 1-10 (10 = highest priority)
- "summary": a one-sentence summary of the request
- "rationale": brief explanation of your classification

Respond ONLY with valid JSON. No markdown, no extra text."""


def get_triage_prompt(pain_point: str, workflow_stage: str, manual_time: str, urgency: str, requester_team: str) -> str:
    return f"""Classify this GTM automation request:

Requester Team: {requester_team}
Pain Point: {pain_point}
Current Workflow Stage: {workflow_stage}
Estimated Manual Time Per Week: {manual_time}
Urgency: {urgency}

Return your classification as JSON."""


# ─────────────────── REQUIREMENTS EXTRACTION ───────────────────

REQUIREMENTS_SYSTEM_PROMPT = """You are a GTM systems engineer who translates vague field requests into structured requirements.

Given a free-text automation request, produce a structured requirements brief with:
- "title": concise project title
- "problem_statement": what problem this solves
- "current_process": how it's done manually today (bullet points)
- "proposed_solution": what the AI/automation should do (bullet points)
- "data_sources": what systems/data are needed
- "success_metrics": how to measure if this worked
- "risks": potential risks or blockers
- "estimated_effort": "Small (1-2 days)", "Medium (1-2 weeks)", or "Large (1+ month)"

Respond ONLY with valid JSON. No markdown, no extra text."""


def get_requirements_prompt(pain_point: str, context: str = "") -> str:
    return f"""Generate a structured requirements brief for this automation request:

Request: {pain_point}
Additional Context: {context}

Return the requirements as JSON."""


# ─────────────────── WORKFLOW BLUEPRINT ───────────────────

BLUEPRINT_SYSTEM_PROMPT = """You are a GTM automation architect. Given a requirements brief, generate a detailed workflow blueprint.

The blueprint should include:
- "workflow_name": descriptive name
- "current_state": list of manual steps in the current process
- "proposed_state": list of AI-assisted steps in the new process
- "integrations": list of systems that need to connect
- "governance": data privacy, PII handling, escalation rules
- "success_metrics": specific KPIs to track
- "rollout_plan": phased rollout steps
- "estimated_time_savings": hours per week

Respond ONLY with valid JSON. No markdown, no extra text."""


def get_blueprint_prompt(title: str, problem: str, requirements: str) -> str:
    return f"""Generate a workflow blueprint for:

Project: {title}
Problem: {problem}
Requirements: {requirements}

Return the blueprint as JSON."""


# ─────────────────── EXECUTIVE SUMMARY ───────────────────

SUMMARY_SYSTEM_PROMPT = """You are a GTM operations leader writing an executive summary for leadership.
Turn raw metrics and project data into a compelling narrative.

Write 2-3 paragraphs covering:
1. What was shipped and why it matters
2. Key results (use the metrics provided)
3. What's next

Keep the tone professional but energetic. Include specific numbers."""


def get_summary_prompt(project_name: str, metrics: str) -> str:
    return f"""Write an executive summary for this GTM AI project:

Project: {project_name}
Metrics: {metrics}

Write a 2-3 paragraph executive narrative."""


# ─────────────────── MOCK RESPONSES ───────────────────

MOCK_TRIAGE_RESPONSE = {
    "gtm_stage": "Pipeline Generation",
    "complexity": "Medium",
    "approach": "AI Agent",
    "priority_score": 7,
    "summary": "Automate lead research to reduce SDR time spent per prospect",
    "rationale": "High manual time investment in a critical pipeline stage; AI agent can handle research aggregation effectively"
}

MOCK_REQUIREMENTS_RESPONSE = {
    "title": "AI-Powered Lead Research Assistant",
    "problem_statement": "SDRs spend 30+ minutes per lead manually researching company info, recent news, and tech stack before outreach.",
    "current_process": [
        "SDR receives new lead assignment",
        "Manually searches LinkedIn, company website, news",
        "Copies relevant info into CRM notes",
        "Drafts personalized outreach based on research"
    ],
    "proposed_solution": [
        "AI agent auto-enriches lead data from multiple sources",
        "Generates research summary with key talking points",
        "Suggests personalized outreach angles",
        "Auto-populates CRM fields"
    ],
    "data_sources": ["Salesforce", "ZoomInfo", "LinkedIn (API)", "Company websites"],
    "success_metrics": ["Reduce research time from 30 min to 5 min per lead", "Increase outreach personalization score", "Improve response rates by 15%"],
    "risks": ["Data freshness of third-party sources", "LinkedIn API rate limits", "PII handling for contact data"],
    "estimated_effort": "Medium (1-2 weeks)"
}

MOCK_BLUEPRINT_RESPONSE = {
    "workflow_name": "Automated Lead Research Pipeline",
    "current_state": [
        "SDR receives lead notification",
        "Opens multiple browser tabs (LinkedIn, company site, news)",
        "Manually reads and extracts key information",
        "Types notes into Salesforce",
        "Drafts email based on research"
    ],
    "proposed_state": [
        "Lead assigned → triggers AI research agent",
        "Agent pulls data from ZoomInfo + company site + news APIs",
        "AI generates structured research brief",
        "Brief auto-attached to Salesforce record",
        "AI suggests 3 personalized outreach angles",
        "SDR reviews, selects angle, sends outreach"
    ],
    "integrations": ["Salesforce CRM", "ZoomInfo API", "News API", "Email platform (Salesloft)"],
    "governance": {
        "pii_handling": "Contact PII stored only in Salesforce, not cached by AI",
        "escalation_rules": "Flag leads from regulated industries for manual review",
        "data_retention": "Research briefs retained for 90 days"
    },
    "success_metrics": ["Time per lead research: 30 min → 5 min", "SDR daily lead capacity: 15 → 40", "Response rate improvement: baseline + 15%"],
    "rollout_plan": ["Week 1: Deploy to 3 pilot SDRs", "Week 2: Gather feedback, iterate prompts", "Week 3: Expand to full SDR team", "Week 4: Measure and report"],
    "estimated_time_savings": "12.5 hours per SDR per week"
}
