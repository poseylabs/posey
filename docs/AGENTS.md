# Agents
We currently have these main agents that are delegated to (some optionally) behind the scenes:

- CONTENT_ANALYZER: (always)
  - an LLM that will analyze user input and decide if any other agents should be delegated to
  - this is called with every request

- MEMORY_AGENT: (always)
  - analyzes users request and determine if anything is important enough to be remembered, and it should search it's memory (vector database) for memories related to the current query

- INTERNET_AGENT: (optional)
  - when delegated to, will use an LLM to generate search queries, then run search with the duckduckgo search API and returns a list of results, and then uses crawl4ai to crawl results

- IMAGE_GENERATOR: (optional)
  - when delegated to, calls an llm to generate a more sophisticated image prompt based on the users input, then it uses flux or user preferred image generator to generate and save an image

- THOUGHT_AGENT: (always)
  - this is the main agent that is used to handle the users request
  - it delegates to the CONTENT_ANALYZER which handles initial analysis and determines if any other agents should be delegated to
  - Creates final response to user based on context of delegation status from agents higher up the chain


## Open-Source Tools, Datasets, and Models

- https://huggingface.co/datasets/gaia-benchmark/GAIA
- https://huggingface.co/papers/2402.01030
