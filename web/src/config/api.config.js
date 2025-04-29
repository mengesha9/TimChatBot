// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/login',
  REGISTER: '/register',
  RESET_PASSWORD: '/reset',
  
  // Chat endpoints
  CHAT: '/chat',
  CHAT_HISTORY: '/chat/history',
  DELETE_CHAT_HISTORY: '/delete-chat-history',
  CLEAR_VECTOR_STORE: '/clear-vector-store',
  
  // Document endpoints
  UPLOAD_PDF: '/upload-pdf',
  GET_PDFS: '/pdfs',
  DELETE_DOC: '/delete-doc'
}; 