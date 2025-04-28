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
      reset_password_db)
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
    """Initialize the application by scraping and indexing NetSuite documentation"""
    try:
        logging.info("Starting to index NetSuite documentation...")
        num_docs = index_netsuite_docs()
        logging.info(f"Successfully indexed {num_docs} NetSuite documentation pages")
    except Exception as e:
        logging.error(f"Error during startup: {str(e)}")
        raise


@app.post("/clear-vector-store")
async def clear_documentation():
    """Clear all documents from the vector store"""
    try:
        success = clear_vector_store()
        if success:
            return {"message": "Successfully cleared vector store"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear vector store")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat-history")
def chat_history(user_id:int):
    return get_user_chat_history(user_id)

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):

    session_id = query_input.session_id  or str(uuid.uuid4())
    print("Session ID: ", session_id)
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")

    chat_history = get_chat_history(session_id,query_input.user_id)
    rag_chain = get_rag_chain(query_input.model.value)
    
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })['answer']

    insert_application_logs(session_id,query_input.user_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, user_id = query_input.user_id, model=query_input.model)

@app.delete("/delete-chat-history")
def delete_chat_history(user_id:int,session_id:str):
    return delete_chat_session(user_id,session_id)

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