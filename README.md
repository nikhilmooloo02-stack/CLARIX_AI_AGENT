# CLARIX — AI Business Operations Agent

> Multimodal AI Agent for SME Customer Support & Product Intelligence
> Built with Python · Anthropic Claude API · ChromaDB · Gradio · Google Colab

---

## What is CLARIX?

CLARIX is a production-ready AI Business Operations Agent designed for South African SMEs. It combines conversational AI with a RAG (Retrieval-Augmented Generation) knowledge base to deliver intelligent customer support and product recommendations in a single deployable system.

Built as a capstone project for the Mentec Foundation Generative AI Certification, CLARIX is deployed for **ShaNeal Distributors** — a stationery, PPE, office equipment, and household consumables distributor based in Pretoria, South Africa.

---

## Key Capabilities

**Customer Support**
- Handles complaints, refund requests, and order queries
- Acknowledges issues with empathy and offers structured solutions
- Automatically escalates high-value or complex cases to human agents
- Maintains full conversation memory throughout the session
- Generates quotations and considers financial metrics 

**Product Intelligence**
- Answers product availability and pricing queries instantly
- Recommends relevant products based on customer needs
- Cross-sells related items naturally like a trained sales assistant
- Calculates bulk order quantities and estimates on request

**RAG Knowledge Base**
- Powered by ChromaDB vector database
- Loaded with ShaNeal's full product catalogue
- Searches and retrieves the most relevant product context on every query
- Eliminates hallucination by grounding responses in real business data

---

## System Architecture
Customer query (text)
Mode detection (support vs product)
RAG search - ChromaDBKnowledge Base
Prompt construction (query, text and history)
Claude-sonnet-4-5 (LLM)
Formatted response - Gradio UI - Customer 



