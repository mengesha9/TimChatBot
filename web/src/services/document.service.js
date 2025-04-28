import axios from "axios";
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.config';

export const uploadDocument = async (file, userId) => {
  try {
  const formData = new FormData();
  formData.append('file', file);
    formData.append('userId', userId);

    const response = await axios.post(
      `${API_BASE_URL}${API_ENDPOINTS.UPLOAD_PDF}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getDocuments = async (userId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.GET_PDFS}/${userId}`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const deleteDocument = async (docId, userId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.DELETE_DOC}`, {
      docId,
      userId,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};
