// categoryApi.js - Handles API calls for categories
import axios from "axios";

const API_URL = "http://127.0.0.1:5000/api/categories";

export const fetchCategories = async () => {
  const response = await axios.get(API_URL);
  return response.data;
};

export const addCategory = async (categoryData) => {
  const response = await axios.post(API_URL, categoryData);
  return response.data;
};

export const updateCategory = async (categoryId, categoryData) => {
  const response = await axios.put(`${API_URL}/${categoryId}`, categoryData);
  return response.data;
};

export const deleteCategory = async (categoryId) => {
  const response = await axios.delete(`${API_URL}/${categoryId}`);
  return response.data;
};
