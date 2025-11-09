# General Tool Usage Guidelines

## Core Principles

**Read Before Edit** - Always use `read_file()` before calling `edit_file()` to understand current content.

**Search Before Create** - Use search tools (`search_articles`, `find_files`) to check if content already exists before creating new files.

**Verify Your Work** - After editing, read the file again to confirm your changes worked as expected.

**Stay Focused** - Use tools with clear intent. Each tool call should advance your current objective.

## Common Patterns

**File Operations:**
- `read_file()` → understand content → `edit_file()` → `read_file()` (verify)
- Use absolute paths or paths relative to wikicontent root

**Article Management:**
- `search_articles()` → `read_article()` → work with content
- Article names can be with or without `.md` extension

**Story Writing:**
- Use `add_to_story()` for sequential narrative that flows
- Use `edit_file()` for surgical edits to specific sections

## Tool Behavior Notes

**Tools that don't emit text:**
- `wait_for_user()` - Pauses immediately, include prompts BEFORE calling
- `done()` - Signals completion, include final message BEFORE calling

**Error Handling:**
- If a tool returns an error, adjust your approach and try again
- Read error messages carefully - they guide you to the solution

## Best Practices

- Make one clear change at a time
- Don't chain too many operations without checking results
- Use descriptive search terms for better results
- Keep file paths consistent and clean

Hunt with purpose. Use tools decisively and effectively!

