import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.agent.service import AgentService

db = SessionLocal()
prompts = [
    "Show me the latest circular about attendance.",
    "Which circular replaced the previous attendance policy?",
    "Which students have not acknowledged the latest attendance circular?",
    "What actions are still pending?",
    "What does the university policy say about attendance?"
]

print("=" * 60)
print("VERIFYING 5 CORE DEMO QUERIES")
print("=" * 60)

for i, p in enumerate(prompts, 1):
    print(f"\n--- DEMO QUERY {i}: \"{p}\" ---")
    res = AgentService.process_query(db, p)
    print(f"Intent:     {res.intent}")
    print(f"Tools Used: {res.tools_used}")
    print(f"Grounded:   {res.grounded}")
    print(f"Sources:    {[s.reference for s in res.sources]}")
    print("Answer:")
    print(res.answer)

db.close()
