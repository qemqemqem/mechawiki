#!/usr/bin/env python3
"""Test context display functionality."""

import sys
sys.path.insert(0, 'src')
import tools

# Load some articles into context to test the display
article_info = tools.story_state.find_existing_article("Lord Dunsany")
if article_info:
    tools.story_state.load_article_to_context(**article_info)

article_info = tools.story_state.find_existing_article("Sultan and Hasheesh-Eater")
if article_info:
    tools.story_state.load_article_to_context(**article_info)

# Display context
context = tools.story_state.get_article_context()
print("📋 Context Display Test:")
print(context)