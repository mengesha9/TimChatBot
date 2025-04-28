import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.config';

export const getChatResponse = async (question, sessionId, model, userId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.CHAT}`, {
      question,
      session_id: sessionId,
      model,
      user_id: userId
    });
    return response.data;
  } catch (error) {
    throw error;
      }
};

export const getChatHistory = async (userId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.CHAT_HISTORY}?user_id=${userId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const deleteChatHistory = async (userId, sessionId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}${API_ENDPOINTS.DELETE_CHAT_HISTORY}?user_id=${userId}&session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const clearVectorStore = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.CLEAR_VECTOR_STORE}`);
    return response.data;
  } catch (error) {
    throw error;
  }
}; 