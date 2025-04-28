import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.config';

export const login = async (email, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.LOGIN}`, {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.REGISTER}`, userData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const resetPassword = async (email) => {
  try {
    const response = await axios.post(`${API_BASE_URL}${API_ENDPOINTS.RESET_PASSWORD}`, {
      email,
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}; 