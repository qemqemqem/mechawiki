# Overall Plan

An AI tool will go through an open source novel -- we'll start with Dracula -- one section at a time. In each section, an LLM will create wikipedia-style content to document it. That will include articles, images, songs, and maybe structured content.

The LLM will be an "agent" in the sense that it will have tool use through MPC.

# Tools (MPC)

* Create article
* Apply edit diff to article
* Create imaage (using DALLE or something)
* Advance story (see below)
* Planned (but not priority 1)
    * Create songs with Suno
    * Create structured data
    * Searching the content

# Technology Stack

* litellm
* fastmpc

# Details

## Chunking the article

Instead of chunking the article totally programmatically, I think we should give the agent a "move forward" tool. when invoked, it will scroll forward the story window by n characters, where n is specified in the tool use.
