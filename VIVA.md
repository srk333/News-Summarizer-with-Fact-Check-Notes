# Viva Questions and Answers

### What is Generative AI?
Generative AI refers to algorithms (like Large Language Models) that can create new content, such as text, code, or images, based on patterns learned from vast amounts of training data.

### Why did you use OpenAI?
OpenAI provides state-of-the-art LLMs (like GPT-4o-mini) that excel at natural language understanding, reasoning, and generating structured JSON outputs required for summarization and fact-checking.

### What is an LLM?
A Large Language Model is an AI model trained on massive amounts of text data. It understands context and generates human-like text by predicting the next most likely word in a sequence.

### What is prompt engineering?
Prompt engineering is the process of designing and refining the instructions given to an LLM to ensure it produces accurate, structured, and relevant outputs while following specific rules (e.g., "Do not invent facts").

### What is RAG?
Retrieval-Augmented Generation (RAG) is a technique that connects an LLM to external data sources. Instead of relying on the LLM's static training knowledge, the system *retrieves* relevant live documents, *augments* the prompt with them, and asks the LLM to *generate* an answer based on that context.

### Why do we need RAG?
LLMs can hallucinate (make things up) and their knowledge cutoff means they don't know current events. RAG grounds the model's answers in real, up-to-date facts.

### What are embeddings?
Embeddings are numerical representations (vectors) of text. They capture semantic meaning, allowing computers to measure how similar two pieces of text are by calculating the distance between their vectors.

### What is vector search?
Vector search is the process of finding the most similar documents to a query by comparing their mathematical vectors (embeddings). It allows searching by meaning rather than exact keyword matches.

### Why did you use FAISS?
FAISS (Facebook AI Similarity Search) is a library optimized for storing embeddings and performing fast similarity searches, making it perfect for retrieving the most relevant evidence chunks in a RAG pipeline efficiently.

### How does fact checking work?
1. Extract claims from the article.
2. Search the web for evidence using Tavily.
3. Process evidence into a vector database.
4. Retrieve the best context chunks for the claim.
5. Ask the LLM to compare the claim against the retrieved chunks and output a verdict.

### How do you identify claims?
We prompt the LLM to read the article and extract only factual statements that can be verified as true or false, strictly ignoring subjective opinions or trivial details.

### How do you retrieve evidence?
We use the Tavily API, which is a search engine optimized for AI agents, to run a web search based on the claim and return the text of the top sources.

### How do you prevent hallucination?
We strictly prompt the LLM: "NEVER use your internal knowledge. Base your decision ONLY on the provided EXTERNAL EVIDENCE." If no evidence is found, the system defaults to "Insufficient Evidence."

### Can the system guarantee that news is true?
No. The system only checks if a claim is supported by other sources on the internet. It cannot mathematically prove truth, as the external sources themselves could be biased or incorrect.

### What happens when no evidence is found?
The system returns a verdict of "Insufficient Evidence" and clearly states that no external sources could be found to verify the claim.

### What is the difference between summarization and fact checking?
Summarization simply condenses what the article *claims* is true. Fact-checking actively searches for external proof to verify *whether* those claims are actually true.

### What are the limitations?
Search results might miss paywalled sites. Scrapers might fail on some websites. AI can misinterpret complex evidence. Lack of evidence doesn't necessarily mean a claim is false.

### What makes this project different from standard ChatGPT?
Standard ChatGPT relies entirely on its pre-trained memory and can hallucinate facts. This project is a specialized pipeline that actively searches the live web, implements a vector database for semantic search, and restricts the AI to only output evidence-based verdicts.
