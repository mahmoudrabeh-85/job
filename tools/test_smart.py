#!/usr/bin/env python3
"""Quick test of smart scoring"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, r"D:\ai\job-hunt\tools")
from job_aggregator import smart_score, analyze_match, should_exclude, load_profile

profile = load_profile()

tests = [
    {
        "name": "Procurement Manager (مطابق تماماً)",
        "job": {"title": "Procurement Manager", "description": "vendor negotiation, supply chain, oracle erp, inventory management", "tags": ["procurement", "supply chain"]}
    },
    {
        "name": "Python Developer (مستبعد)",
        "job": {"title": "Python Developer", "description": "python, django, react, javascript", "tags": ["python", "django"]}
    },
    {
        "name": "Sales Manager - Medical (مطابق جزئياً)",
        "job": {"title": "Sales Manager - Medical Devices", "description": "pharmaceutical sales, business development, key account management", "tags": ["sales", "medical"]}
    },
    {
        "name": "Supply Chain Analyst (مطابق)",
        "job": {"title": "Supply Chain Analyst", "description": "inventory management, logistics, distribution, erp systems", "tags": ["supply chain", "logistics"]}
    },
    {
        "name": "Frontend Developer (مستبعد)",
        "job": {"title": "Frontend Developer React", "description": "javascript, react, typescript, css", "tags": ["react", "javascript"]}
    },
    {
        "name": "Operations Manager (مطابق)",
        "job": {"title": "Operations Manager", "description": "operations management, team leadership, process improvement, cost reduction", "tags": ["operations", "management"]}
    },
]

print("=" * 70)
print(" SMART SCORING TEST")
print("=" * 70)

for test in tests:
    job = test["job"]
    name = test["name"]
    
    excluded, reason = should_exclude(job, profile)
    if excluded:
        print(f"\n{name}")
        print(f"  {reason}")
        continue
    
    score, details = smart_score(job, profile)
    analysis = analyze_match(job, profile)
    
    print(f"\n{name}")
    print(f"  Score: {score}/100 | Match: {analysis['rating']} ({analysis['match_percentage']}%)")
    print(f"  Skills: {len(analysis['matched'])} matched, {len(analysis['partial'])} partial, {len(analysis['missing'])} missing")
    if analysis['matched']:
        print(f"  Top: {', '.join(m['skill'] for m in analysis['matched'][:5])}")
    if analysis['missing']:
        print(f"  Missing: {', '.join(m['skill'] for m in analysis['missing'][:3])}")

print("\n" + "=" * 70)
