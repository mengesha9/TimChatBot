from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from .vector_store_db import vectorstore
from .database import get_chat_history
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("OPENAI_API_KEY: inside the langchain",OPENAI_API_KEY)

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

output_parser = StrOutputParser()


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


print("Dynamic Prompt Text: ",dynamic_prompt_text)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system",dynamic_prompt_text),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


def get_rag_chain(model_name="gpt-4o-mini"):
    llm = ChatOpenAI(model=model_name)
    
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)    
    return rag_chain
