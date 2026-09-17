"""
Institutional Prompt Templates for CircularFlow AI Agent.
Enforces verifiable data grounding, authoritative clarity, and zero policy hallucination.
"""

AGENT_SYSTEM_PROMPT = """You are Cira, the verified Institutional Intelligence Agent for CircularFlow AI.
You assist university executives, registrars, deans, faculty, and students by reasoning over verified institutional records.

CORE RULES:
1. STRICT GROUNDING: State facts derived solely from the provided database and vector knowledge records.
2. NO HALLUCINATION: Never invent circular numbers, dates, student names, or administrative penalties.
3. CITATIONS: Always explicitly reference circular numbers (e.g. `CIR-2026-052`) or policy document names.
4. HONESTY: If a record is not found in the database, clearly explain that no matching verified institutional record exists.
"""


def format_latest_circular_answer(circular: dict) -> str:
    """Formats a grounded summary for a latest circular query."""
    supersession = ""
    if circular.get("supersedes_ref"):
        supersession = f"\n• **Replaces Prior Rule:** Supersedes `{circular['supersedes_ref']}`"

    return (
        f"### Latest Circular: {circular['ref_no']} — {circular['title']}\n\n"
        f"• **Status:** {circular['status']} (Current Active Directive)\n"
        f"• **Department:** {circular['department']}\n"
        f"• **Published Date:** {circular['published_date']} | **Effective Date:** {circular['effective_date']}\n"
        f"• **Category:** {circular['category']} | **Priority:** {circular['priority']}"
        f"{supersession}\n\n"
        f"**Official Summary:**\n{circular['summary']}"
    )


def format_lineage_answer(lineage: dict, target_query: str) -> str:
    """Formats a grounded explanation of supersession and lineage."""
    if not lineage.get("found"):
        return f"The institutional registry does not contain any circular matching `{target_query}`. No supersession record found."

    circ = lineage["circular"]
    superseded = lineage.get("superseded_rule")
    replacement = lineage.get("superseding_replacement")

    lines = [f"### Lineage & Supersession Status: {circ['ref_no']}"]
    lines.append(f"**Circular:** {circ['title']} (Status: `{circ['status']}`)\n")

    if superseded:
        lines.append(
            f"• **Predecessor (Replaced):** This directive **superseded `{superseded['ref_no']}`**"
            f"{(' — ' + superseded['title']) if superseded.get('title') else ''}."
        )
    else:
        lines.append("• **Predecessor:** This is an initial institutional directive (does not supersede earlier circulars).")

    if replacement:
        lines.append(
            f"• **Successor (Active Replacement):** This circular was **superseded by `{replacement['ref_no']}`**"
            f"{(' — ' + replacement['title']) if replacement.get('title') else ''}."
        )
    else:
        lines.append(f"• **Current Validity:** `{circ['ref_no']}` is the currently active, un-superseded directive.")

    return "\n".join(lines)


def format_acknowledgement_answer(data: dict) -> str:
    """Formats an acknowledgement compliance report."""
    if not data.get("found"):
        return data.get("message", "No acknowledgement records found.")

    circ = data["circular"]
    recipients = data.get("recipients", [])
    role_info = f" ({data['role_filter']}s only)" if data.get("role_filter") else ""
    pending_info = " with **Pending** status" if data.get("pending_only") else ""

    lines = [
        f"### Acknowledgement Compliance: {circ['ref_no']}",
        f"**Title:** {circ['title']}",
        f"• **Overall Compliance Rate:** {circ['compliance_rate']}% ({circ['acknowledged_recipients']}/{circ['total_recipients']} confirmed)\n",
        f"**Filtered Recipients{role_info}{pending_info}:**"
    ]

    if not recipients:
        lines.append("• *No recipients match the specified filter.*")
    else:
        for r in recipients:
            status_icon = "⏳" if r["status"] == "Pending" else "✅"
            lines.append(f"• {status_icon} **{r['name']}** — {r['role']} ({r['department']}) | Status: `{r['status']}`")

    return "\n".join(lines)


def format_pending_actions_answer(actions: list) -> str:
    """Formats pending action items."""
    if not actions:
        return "No pending or overdue institutional action items were found in the database."

    lines = [f"### Pending Institutional Action Items ({len(actions)} found)\n"]
    for a in actions:
        p_badge = "🔴 Critical" if a["priority"] == "Critical" else ("🟡 High" if a["priority"] == "High" else "🔵 Normal")
        lines.append(
            f"• **{a['action_id']}: {a['title']}**\n"
            f"  - **Status:** `{a['status']}` | **Priority:** {p_badge}\n"
            f"  - **Responsible:** {a['responsible_role']} ({a['responsible_department']})\n"
            f"  - **Deadline:** {a['deadline']} | **Source:** `{a['source_circular_ref']}`"
        )
    return "\n".join(lines)
