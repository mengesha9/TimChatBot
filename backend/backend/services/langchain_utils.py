from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, Runnable
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from .vector_store_db import vectorstore
from .database import get_chat_history
from .netsuite_scraper import NetSuiteSearch
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

print("OPENAI_API_KEY: inside the langchain", OPENAI_API_KEY)

def get_llm(model: str) -> ChatOpenAI:
    """Get the LLM for the specified model."""
    return ChatOpenAI(
        model=model,
        temperature=0.7,
        streaming=True
    )

def web_search_retriever(query: str) -> List[Document]:
    """
    Search the web using SerpAPI and return relevant documents.
    """
    try:
        print(f"\n🔍 Performing web search for query: {query}")
        # Initialize NetSuiteSearch
        search = NetSuiteSearch(SERPAPI_API_KEY)
        
        # Get search results
        results = search.search_documentation(query)
        print(f"📊 Found {len(results)} search results")
        
        if not results:
            print("⚠️ No results found")
            return []
            
        # Convert results to documents
        docs = []
        for result in results:
            doc = Document(
                page_content=result["content"],
                metadata={
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                    "source": "netsuite_docs"
                }
            )
            docs.append(doc)
            
        print(f"📑 Created {len(docs)} documents")
        return docs
        
    except Exception as e:
        print(f"❌ Error in web search retriever: {str(e)}")
        return []

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Update the prompt file path to use the correct relative path
prompt_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt.txt")
try:
    with open(prompt_file_path, "r") as file:
        dynamic_prompt_text = file.read().strip()
except FileNotFoundError:
    raise Exception(f"Prompt file not found at: {prompt_file_path}")

print("Dynamic Prompt Text: ", dynamic_prompt_text)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", dynamic_prompt_text),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def format_answer(docs: List[Document], query: str, chat_history: List[Dict], llm: ChatOpenAI) -> str:
    """Format the answer using the retrieved documents and chat history."""
    print("\n🤖 Formatting answer...")
    # Create a prompt for the answer
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Use the following context to answer the question. "
                  "Make sure to provide accurate and relevant information based on the context."),
        ("system", "Context: {context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    # Format the context from documents
    context = "\n\n".join([doc.page_content for doc in docs])
    print(f"📚 Using {len(docs)} document chunks as context")
    
    # Convert chat history to list of messages
    messages = []
    for msg in chat_history:
        if msg["role"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
    print(f"💬 Including {len(chat_history)} previous conversation turns")
    
    # Get the answer
    print("🤔 Generating response...")
    answer_chain = answer_prompt | llm
    response = answer_chain.invoke({
        "context": context,
        "chat_history": messages,
        "question": query
    })
    
    print("✅ Response generated successfully")
    return response.content

def get_rag_chain(model: str) -> Runnable:
    """Get the RAG chain for the specified model."""
    print(f"\n🔄 Initializing RAG chain with model: {model}")
    llm = get_llm(model)
    
    # Create a custom retriever that uses web search
    def custom_retriever(query: str) -> List[Document]:
        return web_search_retriever(query)
    
    # Create a reformulation function that uses the LLM
    def reformulate_question(query: str, chat_history: List[Dict]) -> str:
        if not chat_history:
            print("📝 No chat history, using original query")
            return query
            
        print("\n🔄 Reformulating question based on chat history...")
        print(f"💬 Using {len(chat_history)} previous conversation turns")
        # Create a prompt for reformulation
        reformulation_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that reformulates questions based on chat history. "
                      "Your goal is to make the question more specific and clear by incorporating context from the chat history."),
            ("human", "Chat History:\n{chat_history}\n\nCurrent Question: {question}\n\nReformulated Question:")
        ])
        
        # Format chat history
        formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
        print(f"📝 Previous conversation:\n{formatted_history}")
        
        # Get reformulated question
        reformulation_chain = reformulation_prompt | llm
        reformulated = reformulation_chain.invoke({
            "chat_history": formatted_history,
            "question": query
        })
        
        print(f"📝 Reformulated question: {reformulated.content}")
        return reformulated.content
    
    # Create the RAG chain
    print("🔗 Creating RAG chain...")
    rag_chain = (
        {
            "input": lambda x: x["input"],
            "chat_history": lambda x: x.get("chat_history", [])
        }
        | RunnablePassthrough.assign(
            reformulated_question=lambda x: reformulate_question(x["input"], x["chat_history"])
        )
        | RunnablePassthrough.assign(
            docs=lambda x: custom_retriever(x["reformulated_question"])
        )
        | {
            "answer": lambda x: format_answer(x["docs"], x["input"], x["chat_history"], llm),
            "docs": lambda x: x["docs"]
        }
    )
    
    print("✅ RAG chain initialized successfully")
    return rag_chain
