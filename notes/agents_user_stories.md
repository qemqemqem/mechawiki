This is a project to use AI to write stories, in both a fully autonomous way and in an interactive way. The core implementational idea is that these are implemented as AI agents that use tools. I’ll talk more about the implementation later. This page is about their use. 

Throughout this project, there will be an interplay between stories as prose and structured data and encyclopedic wiki style content about that story. 

There are several agents at focus in this system, and they are:

- Reader Agent
- Writer Agent
- Interactive Agent
- Researcher Agent

Together, these systems will allow the user to take an existing story and convert it into more structured content, or to take more structured content and convert it into a story which is either interactive or not. 

These are collectively referred to as the Story Agents. 

# Reader Agent

The reader agent’s job is to read through a story and produce encyclopedic content about it. Sort of the opposite of using an AI to write a story. 

## Use

The envisioned use of the Reader Agent is that the user will use it to take a source text and structure it. That source text might be an existing story or novel, or it might be the user’s notes about a story that they wish to write. 

The Reader will produce by the time it’s done a corpus of documentation that can be used by the other agents. 

## Inputs

As input, the Reader agent takes in a story. Imagine a large out of copywrite novel such as Dracula or Tales of Wonder. This source novel might exceed the context length of an LLM, so the agent will have the ability to *advance* the story, requesting more content in incremental fashion. This will allow the agent to focus on one part of the story at a time.

<aside>
💡

Make the context window indices available to the agent and include them in the comments with any committed change so we link whatever source text triggered a set of changes. 

The reader agent will also need to be able to find all the content relevant to the text it is processing so that it can edit existing articles as well as make new ones. This should likely be done using keyword, vector embedding and link based searches. 

Edits should link no only the relevant source text but also the relevant wiki text so that when we edit the wiki later we can find other places on the text might need to change and propegate changes via the links. 

</aside>

## Outputs

The Reader Agent’s job is to document the story in sufficient detail that it could be recreated or reimagined. The reader should write encyclopedic text in a neutral style. In addition, it should document compelling prose such as memorable dialog or descriptions. 

The reader agent takes in text, but it may produce images or audio, such as songs. This will necessarily involve acts of imagination as performed by an AI. Much of the heavy lifting will be performed by a networked service available through MCP. But, the reader agent will be required to produce compelling image or audio prompts. When doing so, it should blend an encyclopedic documentary goal with a creative, entertaining goal. 

See [Content Structure](https://www.notion.so/Content-Structure-2841964d3d4580d3a15be0d3387fc257?pvs=21) (Content Structure) for more details about this. 

# Writer Agent

The Writer is essentially the opposite of the Reader. Its job is to take structured content as input, and write a story. Its inputs will exactly be the same structure as what is produced by the Reader. 

## Use: Structured Content to Story

The user may call upon the Writer to take structured content and produce a compelling story. The poster use case for this is that the user may upload their own documentation about a story they’ve been working on, and the writer would produce a story about it. Or alternatively, the user might upload a text like *Hamlet* to the Reader, and then ask the Writer to “write a story from the POV of Ophelia”. 

## Use: Writing a Story from Scratch

In some cases, the user’s documentation may be very scarce, or they may have only the thinnest premise for a story. In that case, in order to produce a strong story that maintains narrative and thematic consistency across a long stretch, the Writer should keep notes as it goes. 

A long story may exceed the context length of an LLM, and even when it doesn’t, research has shown that 2025 era LLMs struggle to produce long stories. So it’s very important that the Writer maintain good notes as it goes. These notes may document plot elements, like the names and details of a character, or they might document thematic elements, like philosophical themes. See the Content Structure note for more. 

In this use case demonstrates how the Writer will always alternate between writing prose and notes for itself. 

## Multi-Modal Stories

If the structured data includes it, the Writer may include images, sound effects, songs, or other multimodal content in the story that it writes. 

# Interactive Agent

The Interactive Agent creates a roleplaying game like experience for the user, turning them into the player. 

It’s like the Writer, but instead of being fully autonomous, it asks the user for input sometimes. Most likely, it casts the user as the main character, and periodically asks them for input on what the character does. 

Depending on the type of story, the user may be able to act as any one of the POV characters. Or perhaps the user is consulted on certain types of questions. The Interactive Agent should decide with the user at the beginning what kind of interaction there will be, and clarify this as a core detail about the story. 

Just like the Writer, Interactive mode may include multimodal content.

In Interactive mode, it is important to reduce latency, so the Interactive Agent should prefer to use existing content rather than commissioning new art or audio on the fly. Ideally the agent can steer the user towards pre generated content but the intent is to allow players the full flexibility to go off the rails and roleplay their character as they intend so it must be able to improvise coherently within the established facts. 

# Researcher Agent

The Researcher is meant to act as a background agent alongside the Interactive Agent and the Writer Agent to create structured content while the user is reading or interacting, in order to reduce latency. 

The Researcher will not be used directly by the user. Instead, it will be used by another agent. This will need to include some message passing, which will be discussed in more detail when we get to implementation. 

A typical request might come from the Interactive Agent, and it might say something like the following:

> “The user is taking the story to Budapest in the year 1430. I don’t have any material prepared for that. Please research that location, and create locations, characters, and plot lines. Include images. Please message me back with the titles of files as you create them.”
> 

The researcher should use a mixture of web searching, searching local files, and imagination to create this content. 

# Recorder Agent

The Recorder is another asynchronous agent meant to support the Interactive Agent to reduce lag times for the player. 

The Recorder takes in a stream of interactions from the interactive session and makes notes about them. It’s basically like the Reader but it’s taking as input the stream of interactions between the user and the Interactive Agent instead of reading a preexisting story. In practice this can be nearly identical to the reader and just process new chunks of text as they are appended to the ongoing story logs.