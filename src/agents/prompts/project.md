# MechaWiki Project

MechaWiki is an AI-powered storytelling and wiki generation system where specialized agents work collaboratively to read stories, write stories, and create interactive experiences.

## Core Concept

The system combines narrative creation with structured wiki-style documentation. Agents operate on a shared content repository (`wikicontent`), maintaining consistency through markdown articles about characters, locations, events, and themes.

## Agent Ecosystem

Three specialized agent types form the foundation:
- **ReaderAgent** - Analyzes existing stories chunk-by-chunk, extracting key elements and creating wiki documentation
- **WriterAgent** - Synthesizes wiki content into compelling narrative prose
- **InteractiveAgent** - Creates RPG-style experiences where users make choices that shape the story

## Content Management

All content lives in a git-managed `wikicontent` repository:
- **Articles** - Markdown files documenting story elements
- **Stories** - Narrative prose files
- **Images** - Generated visuals (when enabled)
- **Audio** - Music and sound content (when applicable)

Agents reference articles to maintain world consistency and create new articles as they discover or invent story elements.

## Philosophy

Hunt with purpose. Work with intensity. Build content that matters.

