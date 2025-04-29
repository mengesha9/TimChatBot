from fastapi import FastAPI, File, UploadFile, HTTPException
from .models.pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from fastapi.security import OAuth2PasswordBearer
from .models.user import UserRegister
from .services.langchain_utils import get_rag_chain
from .services.database import (
      insert_application_logs,
      get_chat_history, get_all_documents, 
      insert_document_record, 
      delete_document_record,
      get_user_by_email,
      insert_user,
      get_user_chat_history,
      delete_chat_session,
      reset_password_db,
      delete_chat_history)
from .services.vector_store_db import index_document_to_chroma, delete_doc_from_chroma, index_netsuite_docs, clear_vector_store
from .services.auth import decode_token, hash_password, create_access_token,verify_password
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import logging
import shutil
from typing import Dict, List

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Document formats
allowed_extensions = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.csv', '.txt',
    '.jpeg', '.jpg', '.png',
    '.html'
]

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        logging.info("Starting application...")
        # Check if required environment variables are set
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception("OPENAI_API_KEY environment variable is not set")
        if not os.getenv("SERPAPI_API_KEY"):
            raise Exception("SERPAPI_API_KEY environment variable is not set")
        logging.info("Application started successfully")
    except Exception as e:
        logging.error(f"Error during startup: {str(e)}")
        raise

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    # Comment out session ID generation for now
    # session_id = query_input.session_id or str(uuid.uuid4())
    session_id = "global_session"  # Use a constant session ID for now
    print(f"\n🆕 Session ID: {session_id}")
    print(f"👤 User Query: {query_input.question}")
    print(f"🤖 Model: {query_input.model.value}")

    # Get chat history without session ID
    chat_history = get_chat_history()
    print(f"💬 Retrieved {len(chat_history)} previous conversation turns")
    
    # Initialize RAG chain
    rag_chain = get_rag_chain(query_input.model.value)
    
    # Get answer
    print("\n🔄 Processing query through RAG chain...")
    answer = rag_chain.invoke(
        {
            "input": query_input.question,
            "chat_history": chat_history
        }
    )['answer']

    # Log the interaction
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    print(f"✅ Response generated and logged")
    print(f"📝 AI Response: {answer}")
    
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post("/register")
def register(user:UserRegister):
    hashed_password = hash_password(user.password)

    insert_user(user.email, hashed_password)
    response= get_user_by_email(user.email)
    token = create_access_token(data={"sub": response["id"]})
    return {"access_token": token, "token_type": "bearer", "user_id": response["id"]}

@app.post("/login")
def login(userlogin:UserRegister):
    user = get_user_by_email(userlogin.email)
    if not user or not verify_password(userlogin.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user["id"]})
    response = {"access_token": token, "token_type": "bearer", "user_id": user["id"]}
    return response

@app.post("/reset")
async def reset_password(request: UserRegister):
    user = get_user_by_email(request.email)
    if user:
        hashed_password = hash_password(request.password)
            
        return reset_password_db(request.email, hashed_password)
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.delete("/chat/history")
def delete_all_chat_history():
    """Delete all chat history"""
    success = delete_chat_history()
    if success:
        return {"message": "All chat history deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete chat history")

@app.delete("/chat/history/{session_id}")
def delete_session_chat_history(session_id: str):
    """Delete chat history for a specific session"""
    success = delete_chat_history(session_id)
    if success:
        return {"message": f"Chat history for session {session_id} deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete chat history")