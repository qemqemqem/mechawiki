These agents will follow a modern tool-using LLM architecture, in which the LLM outputs text, uses tools, and receives answers from the tools. These messages will accumulate in the agent’s memory. Periodically, the memory may need to be consolidated for context window reasons. 

The project may use tools such as these, but please speak with me about them before implementing:

- Litellm tool calling
- Mastra (new AI agents framework)
- Claude Agents SDK
- Model Context Protocol

These tools should use best practices for agents at the time of work. If you aren’t sure what those best practices are, please research them. 

# Tools

Tool use is a key element of AI agents such as these. The essential flow of these agents is that they emit tokens sequentially, in chunks. Sometimes a chunk of tokens will include a tool invocation. When that happens, LLM output will be halted, the tool will be invoked, and the tool’s return content will be injected into the LLM output, and it will be restarted. Each tool is essentially a function, which may or may not have side effects. 

Even user interaction is likely to be handled as a tool. n this framework, the LLM never really stops, it just uses a tool to indicate that it would like feedback from the user. The researcher agent may use a tool to indicate that it is done for now, and it is waiting for further messages to arrive asynchronously from another agent. Similarly, the  Researcher will use a tool to send a message back to whoever commissioned it for research. 

Please see the note about agents use cases for a summary of what the agents are like from the user’s perspective. 

# Local Content

In the following tools, it is assumed that there are local files representing aspects of the story. Please see the note about Content Structure for more details. But assume the following exists:

- The story, such as `story.txt`, at least for the Reader agent. This might be like Dracula or Huckleberry Finn
- Text (`.md`) files representing encyclopedic content about the plot or the setting. These will have frontmatter at the top to store metadata
- Text (`.md`) files with author’s notes about the story. See the note about Writing Strategies to see how to use these
- Image files. These may have informative names, or some kind of metadata, but they should also be referenced by the encyclopedia entries
- Audio files. These will be sound effects or songs
- JSON structured data. In some cases, a story may be well-served by explicitly structured data. For example, a character in a LitRPG may have stats, or an especially structured story may use spreadsheet-like data. I’m not sure if this is a good idea, but it could be!

# Reader Agent

The Reader has these basic tools:

- Read story at position N — Get a chunk of words from the story at a certain position.
- Advance the story — read the next chunk of story, automatically advancing from wherever the last place it read was
- Read a local file — read a .md file that includes notes about the plot, setting, or authorial intention or plans
- Search local files — `grep` in the contents or `find` in the file names for files that match some search terms. Possibly including vector similarity, if the tooling supports it easily. This may also include search results from `story.txt` as well
- Read local files — write out edits to local files. For example, while reading Tales of Wonder, the reader agent may learn that a character has a profession. They should edit that character’s page to include that detail
- Commission and store an image — when writing the page for Alucard, the Reader may decide the page would be improved with an image. Perhaps the text has some evocative imagery. This tool will use DALLE, Midjourney, or another image generation tool to create an art piece
- Commission and store audio — similar to an image. This may not be available in v0, depending on tooling
- Commission and store video — this will not be available in v0, but will be in the future

# Writer Agent

The Writer has most of the tools of the Reader, but it lacks “advance the story” — it advances the story by writing it! It also has:

- Write story — emit actual prose, to add onto the story being written. The text here will be appended to the end of `story.txt`!
- Edit story — the Writer can edit `story.txt` directly. This will enable it to “go back” and revise earlier parts of the story

# Interactive Agent

The Interactive Agent is kind of like the Writer. It has the same subset of Reader tools that Writer has, but it has slightly different output tools.

- Send prose to user — this is a lot like the “write story” tool. But instead of appending text to `story.txt`, the text will be shown to the user. The prompting should be slightly different here, because the nature of good prose is different when the user is interacting
- Request user input — ask the user what they want to do. For example, the agent might send prose to the user describing a large bull snorting and approaching the main character, then ask the user what that character does. It may be appropriate to use the second person “you” when asking the user in this way, but that is an editorial choice. It is up to the Interactive Agent to roll with the user’s input and continue the story in such a way as to incorporate it
- RPG subsystem — sometimes Interactive mode will be set up such that the user is “playing an RPG”, and in that case, the Interactive Agent may want to use a tool to decide the results of an action. For example, if the user asserts that they will shoot the sneaky goblin with their rocket launcher, the RPG may be consulted to check whether the character has a rocket launcher and the skill needed to make the shot. This will not be available in v0.

Notably, it lacks “edit story” — in Interactive mode, you can’t go back!

If the Researcher is enabled, then the Interactive Agent may lack the ability to commission art or audio. Those tools have high latency, and it would be better if they occurred in the background. 

# Researcher Agent

The Researcher has certain tools. When a Researcher is enabled and operating in the background, the Interactive Agent will gain additional tools as well. 

The Interactive Agent will gain these tools:

- Send request to researcher — a request might be something like “create an engaging plot line centered around stealing the Fire Jewel, including several fiery characters and art assets”

The Researcher agent will also have all of the tools of the Reader. This will enable it to create content. 

It is expected to, and should be prompted to, send regular updates back to the Interactive Agent about its progress creating assets. 

The Researcher also has the tool:

- Wait for input — do nothing until an incoming message comes in

The researcher should exist in a separate process in the background. 

# Recorder Agent

The Recorder agent is intended to be a background agent, like the Researcher, to support the Interactive Agent. 

It has all of the tools available to Reader Agent, but instead of “advance the story”, it has:

- Wait for story — wait idly in the background until the active Interactive Agent logs more unfolding events

The Recorder is not intended to have message passing. 

Neither the Researcher nor the Recorder will be implemented in v0.