import logging
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from app.core.config import get_settings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import HumanMessage, AIMessage

settings = get_settings()
logger = logging.getLogger("devmind.chain")

# ── Prompts ────────────────────────────────────────────────────────────────

CODE_REVIEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert code reviewer. Analyze the given code and provide:

1. **Summary**: What the code does (2-3 lines)
2. **Issues**: Bugs, anti-patterns, security concerns (list each clearly)
3. **Suggestions**: Specific improvements with short code examples
4. **Rating**: X/10 with one-line reasoning

Keep it concise and actionable. Use markdown formatting."""),
    ("human", "Language: {language}\n\nCode:\n```{language}\n{code}\n```"),
])

RAG_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful coding assistant with access to the
user's code review history. Use the retrieved context below to answer.
If context is insufficient, say so — do not hallucinate.

--- Retrieved Context ---
{context}
--- End Context ---"""),
    MessagesPlaceholder("chat_history"),    # ← memory slot
    ("human", "{question}"),
])

# ── LLM factory ────────────────────────────────────────────────────────────

def get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model="llama-3.1-8b-instant",   # Free tier ~14K req/day, ~800 tok/sec
        temperature=0.3,
        max_tokens=1024,
    )


# ── Chain factories ────────────────────────────────────────────────────────

def get_review_chain():
    """Direct LLM chain — no retrieval for fresh reviews."""
    return CODE_REVIEW_PROMPT | get_llm() | StrOutputParser()



async def get_rag_chain_with_context(
    context: str,
    question: str,
    chat_history: list = None,
) -> str:
    """
    Context comes in from outside (already retrieved in service layer).
    No internal similarity search — that's done once in review_service.py.
    """
    llm = get_llm()
    history = chat_history or []

    prompt_value = RAG_QA_PROMPT.format_messages(
        context=context,
        question=question,
        chat_history=history,
    )
    response = await llm.ainvoke(prompt_value)
    return response.content