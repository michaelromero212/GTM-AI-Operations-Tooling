"""
FastAPI Web Application — GTM AI Operations Hub
Routes: Overview, Intake, Backlog, Builder, Impact, AI Status
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.agent import GTMOpsAgent
from data.seed import initialize_database, DB_PATH

# ─────────── App Setup ───────────

app = FastAPI(title="GTM AI Operations Hub")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Initialize agent and database
agent = GTMOpsAgent()
_db_initialized = False


def get_db() -> duckdb.DuckDBPyConnection:
    """Get a database connection, initializing on first call."""
    global _db_initialized
    if not _db_initialized:
        initialize_database()
        _db_initialized = True
    return duckdb.connect(DB_PATH)


# ─────────── API Endpoints ───────────


@app.get("/api/ai-status")
async def ai_status():
    """Check AI/LLM connection health by pinging HuggingFace."""
    result = agent.check_health()
    return JSONResponse(result)


# ─────────── Page Routes ───────────


@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    """Platform overview — summary stats and recent activity."""
    try:
        con = get_db()
        # Summary stats
        total_requests = con.execute("SELECT COUNT(*) FROM intake_requests").fetchone()[0]
        in_progress = con.execute("SELECT COUNT(*) FROM backlog_items WHERE status IN ('Scoping', 'In Build', 'QA')").fetchone()[0]
        deployed = con.execute("SELECT COUNT(*) FROM backlog_items WHERE status IN ('Deployed', 'Measuring')").fetchone()[0]
        total_time_saved = con.execute("SELECT COALESCE(SUM(manual_time_before - ai_time_after), 0) FROM impact_metrics WHERE weeks_deployed > 0").fetchone()[0]

        # Status breakdown
        status_counts = con.execute("""
            SELECT status, COUNT(*) as count
            FROM backlog_items GROUP BY status ORDER BY count DESC
        """).fetchdf().to_dict("records")

        # Team breakdown
        team_counts = con.execute("""
            SELECT requester_team, COUNT(*) as count
            FROM intake_requests GROUP BY requester_team ORDER BY count DESC
        """).fetchdf().to_dict("records")

        # Recent activity (Triage requests)
        recent = con.execute("""
            SELECT id, requester_name, requester_team, triage_summary, urgency, status, created_at
            FROM intake_requests ORDER BY created_at DESC LIMIT 5
        """).fetchdf().to_dict("records")

        # Live Event Stream (Audit log)
        audit_entries = con.execute("""
            SELECT event_type, description, CAST(timestamp AS VARCHAR) as timestamp
            FROM audit_log ORDER BY timestamp DESC LIMIT 5
        """).fetchdf().to_dict("records")

        con.close()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "total_requests": total_requests,
            "in_progress": in_progress,
            "deployed": deployed,
            "total_time_saved": round(total_time_saved, 1),
            "status_counts": status_counts,
            "team_counts": team_counts,
            "recent": recent,
            "audit_entries": audit_entries,
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, "error": str(e),
            "total_requests": 0, "in_progress": 0, "deployed": 0,
            "total_time_saved": 0, "status_counts": [], "team_counts": [], "recent": [],
        })


@app.get("/intake", response_class=HTMLResponse)
async def intake_page(request: Request):
    """Intake Triage Queue — view and manage automated ingestions."""
    try:
        con = get_db()
        # Fetch requests that are still in 'Intake' or 'Scoping' for triage
        queue = con.execute("""
            SELECT id, requester_name, requester_team, triage_summary, urgency, status, created_at
            FROM intake_requests 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchdf().to_dict("records")
        con.close()
        
        return templates.TemplateResponse("intake.html", {
            "request": request, 
            "queue": queue,
            "result": None, 
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("intake.html", {
            "request": request, "queue": [], "result": None, "error": str(e),
        })


@app.post("/intake", response_class=HTMLResponse)
async def intake_submit(
    request: Request,
    requester_name: str = Form(...),
    requester_team: str = Form(...),
    pain_point: str = Form(...),
    workflow_stage: str = Form(...),
    manual_time_hours: float = Form(...),
    urgency: str = Form("Medium"),
):
    """Process intake form — LLM triage + save to DB."""
    try:
        # Triage with AI
        triage = agent.triage_request(
            pain_point=pain_point,
            workflow_stage=workflow_stage,
            manual_time=f"{manual_time_hours} hours/week",
            urgency=urgency,
            requester_team=requester_team,
        )

        req_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate requirements brief
        requirements = agent.generate_requirements(pain_point)

        # Save intake request
        con = get_db()
        con.execute("""
            INSERT INTO intake_requests
            (id, requester_name, requester_team, pain_point, workflow_stage,
             manual_time_hours, urgency, created_at, gtm_stage, complexity,
             approach, priority_score, triage_summary, requirements_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Intake')
        """, [
            req_id, requester_name, requester_team, pain_point, workflow_stage,
            manual_time_hours, urgency, now,
            triage.get("gtm_stage", "Unknown"),
            triage.get("complexity", "Unknown"),
            triage.get("approach", "Unknown"),
            triage.get("priority_score", 5),
            triage.get("summary", pain_point[:100]),
            json.dumps(requirements),
        ])

        # Create backlog item
        blg_id = f"BLG-{uuid.uuid4().hex[:6].upper()}"
        con.execute("""
            INSERT INTO backlog_items
            (id, request_id, title, requester_name, requester_team, gtm_stage,
             complexity, approach, priority_score, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Intake', ?, ?)
        """, [
            blg_id, req_id,
            triage.get("summary", pain_point[:60]),
            requester_name, requester_team,
            triage.get("gtm_stage", "Unknown"),
            triage.get("complexity", "Unknown"),
            triage.get("approach", "Unknown"),
            triage.get("priority_score", 5),
            now, now,
        ])
        con.close()

        return templates.TemplateResponse("intake.html", {
            "request": request,
            "result": {
                "request_id": req_id,
                "triage": triage,
                "requirements": requirements,
                "source": triage.get("_source", "unknown"),
                "latency_ms": triage.get("_latency_ms", 0),
            },
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("intake.html", {
            "request": request, "result": None, "error": str(e),
        })


@app.get("/backlog", response_class=HTMLResponse)
async def backlog_page(request: Request, team: str = "", status: str = ""):
    """Kanban-style backlog board."""
    try:
        con = get_db()

        # Build filter query
        where_clauses = []
        params = []
        if team:
            where_clauses.append("requester_team = ?")
            params.append(team)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        items = con.execute(f"""
            SELECT * FROM backlog_items {where_sql}
            ORDER BY priority_score DESC, created_at DESC
        """, params).fetchdf().to_dict("records")

        # Group by status for Kanban columns
        columns = {
            "Intake": [], "Scoping": [], "In Build": [],
            "QA": [], "Deployed": [], "Measuring": [],
        }
        for item in items:
            col = item.get("status", "Intake")
            if col in columns:
                columns[col].append(item)

        # Get unique teams for filter
        teams = con.execute("SELECT DISTINCT requester_team FROM backlog_items ORDER BY requester_team").fetchdf()["requester_team"].tolist()
        con.close()

        return templates.TemplateResponse("backlog.html", {
            "request": request,
            "columns": columns,
            "teams": teams,
            "active_team": team,
            "active_status": status,
            "total_items": len(items),
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("backlog.html", {
            "request": request,
            "columns": {k: [] for k in ["Intake", "Scoping", "In Build", "QA", "Deployed", "Measuring"]},
            "teams": [], "active_team": "", "active_status": "", "total_items": 0,
            "error": str(e),
        })


@app.post("/backlog/update")
async def backlog_update(item_id: str = Form(...), new_status: str = Form(...)):
    """Move a backlog item to a new status column."""
    try:
        con = get_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute(
            "UPDATE backlog_items SET status = ?, updated_at = ? WHERE id = ?",
            [new_status, now, item_id],
        )
        con.close()
        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/builder/{request_id}", response_class=HTMLResponse)
async def builder_page(request: Request, request_id: str):
    """Workflow builder for a specific request."""
    try:
        con = get_db()
        req = con.execute("SELECT * FROM intake_requests WHERE id = ?", [request_id]).fetchdf()
        if len(req) == 0:
            con.close()
            return templates.TemplateResponse("builder.html", {
                "request": request, "item": None, "error": "Request not found",
                "blueprint": None, "prompt_versions": [],
            })

        item = req.to_dict("records")[0]

        # Get prompt versions
        versions = con.execute("""
            SELECT * FROM prompt_versions WHERE request_id = ?
            ORDER BY version DESC
        """, [request_id]).fetchdf().to_dict("records")

        con.close()

        # Parse stored requirements
        requirements = None
        if item.get("requirements_json"):
            try:
                requirements = json.loads(item["requirements_json"])
            except json.JSONDecodeError:
                pass

        return templates.TemplateResponse("builder.html", {
            "request": request,
            "item": item,
            "requirements": requirements,
            "blueprint": None,
            "prompt_versions": versions,
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("builder.html", {
            "request": request, "item": None, "error": str(e),
            "blueprint": None, "prompt_versions": [],
        })


@app.post("/builder/{request_id}/generate")
async def builder_generate(request: Request, request_id: str):
    """Generate a workflow blueprint using LLM."""
    try:
        con = get_db()
        req = con.execute("SELECT * FROM intake_requests WHERE id = ?", [request_id]).fetchdf()
        if len(req) == 0:
            con.close()
            return JSONResponse({"success": False, "error": "Request not found"}, status_code=404)

        item = req.to_dict("records")[0]
        con.close()

        # Parse requirements
        req_text = item.get("requirements_json", "")
        if req_text:
            try:
                req_data = json.loads(req_text)
                req_text = json.dumps(req_data, indent=2)
            except json.JSONDecodeError:
                pass

        blueprint = agent.generate_blueprint(
            title=item.get("triage_summary", ""),
            problem=item.get("pain_point", ""),
            requirements=req_text,
        )

        return JSONResponse({"success": True, "blueprint": blueprint})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/builder/{request_id}/prompt-lab")
async def prompt_lab_submit(
    request: Request,
    request_id: str,
    prompt_text: str = Form(...),
):
    """Submit a prompt to the Prompt Lab and save the version."""
    try:
        con = get_db()

        # Get next version number
        max_ver = con.execute(
            "SELECT COALESCE(MAX(version), 0) FROM prompt_versions WHERE request_id = ?",
            [request_id],
        ).fetchone()[0]
        new_ver = max_ver + 1

        # Call LLM with custom prompt
        from agent.prompts import TRIAGE_SYSTEM_PROMPT
        raw = agent._call_llm(
            "You are an AI operations assistant. Respond helpfully to the following prompt.",
            prompt_text,
        )
        response_text = raw or "[Mock response] The AI agent would process this prompt and return a structured output based on the task type and context provided."

        # Save version
        pv_id = f"PV-{uuid.uuid4().hex[:6].upper()}"
        con.execute("""
            INSERT INTO prompt_versions (id, request_id, version, prompt_text, response_text)
            VALUES (?, ?, ?, ?, ?)
        """, [pv_id, request_id, new_ver, prompt_text, response_text])
        con.close()

        return JSONResponse({
            "success": True,
            "version": new_ver,
            "response": response_text,
            "source": "llm" if raw else "mock",
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/governance", response_class=HTMLResponse)
async def governance_page(request: Request):
    """AI Governance & QA — audit trail, QA checks, prompt versioning."""
    try:
        con = get_db()

        # Audit log (recent 20)
        audit_entries = con.execute("""
            SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 20
        """).fetchdf().to_dict("records")

        # QA checks
        qa_results = con.execute("""
            SELECT * FROM qa_checks ORDER BY run_at DESC
        """).fetchdf().to_dict("records")

        # Aggregate stats
        total_events = con.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        qa_total = con.execute("SELECT COUNT(*) FROM qa_checks").fetchone()[0]
        qa_passed = con.execute("SELECT COUNT(*) FROM qa_checks WHERE status = 'pass'").fetchone()[0]
        qa_pass_rate = round((qa_passed / qa_total * 100), 1) if qa_total > 0 else 0

        avg_quality = con.execute("""
            SELECT COALESCE(AVG(quality_score), 0) FROM prompt_versions WHERE quality_score > 0
        """).fetchone()[0]

        active_workflows = con.execute("""
            SELECT COUNT(DISTINCT request_id) FROM qa_checks
        """).fetchone()[0]

        con.close()

        return templates.TemplateResponse("governance.html", {
            "request": request,
            "audit_entries": audit_entries,
            "qa_results": qa_results,
            "total_events": total_events,
            "qa_pass_rate": qa_pass_rate,
            "avg_quality": round(avg_quality, 1),
            "active_workflows": active_workflows,
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("governance.html", {
            "request": request, "audit_entries": [], "qa_results": [],
            "total_events": 0, "qa_pass_rate": 0, "avg_quality": 0,
            "active_workflows": 0, "error": str(e),
        })


@app.get("/impact", response_class=HTMLResponse)
async def impact_page(request: Request):
    """Impact tracker dashboard."""
    try:
        con = get_db()

        metrics = con.execute("""
            SELECT * FROM impact_metrics ORDER BY weeks_deployed DESC
        """).fetchdf().to_dict("records")

        # Aggregate stats
        total_time_saved = con.execute("""
            SELECT COALESCE(SUM(manual_time_before - ai_time_after), 0)
            FROM impact_metrics WHERE weeks_deployed > 0
        """).fetchone()[0]

        total_roi = con.execute("""
            SELECT COALESCE(SUM(roi_estimate), 0) FROM impact_metrics WHERE weeks_deployed > 0
        """).fetchone()[0]

        avg_adoption = con.execute("""
            SELECT COALESCE(AVG(adoption_rate), 0) FROM impact_metrics WHERE weeks_deployed > 0
        """).fetchone()[0]

        deployed_count = con.execute("""
            SELECT COUNT(*) FROM impact_metrics WHERE weeks_deployed > 0
        """).fetchone()[0]

        con.close()

        return templates.TemplateResponse("impact.html", {
            "request": request,
            "metrics": metrics,
            "total_time_saved": round(total_time_saved, 1),
            "total_roi": round(total_roi, 0),
            "avg_adoption": round(avg_adoption, 1),
            "deployed_count": deployed_count,
            "error": None,
        })
    except Exception as e:
        return templates.TemplateResponse("impact.html", {
            "request": request, "metrics": [], "error": str(e),
            "total_time_saved": 0, "total_roi": 0, "avg_adoption": 0, "deployed_count": 0,
        })

