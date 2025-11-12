#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test query database for activities"""
import os
import sys
import django
import asyncio
from pathlib import Path

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from agents.travel_agents.activities_agent import ActivitiesAgent

async def test():
    agent = ActivitiesAgent()
    result = await agent._query_fallback_activities_from_db('Vũng Tàu')
    print(f'Kết quả: {len(result)} activities')
    for a in result[:5]:
        print(f"  - {a['name']}: {a.get('description', '')[:50]}...")

asyncio.run(test())

