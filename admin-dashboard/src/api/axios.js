// src/api/axios.js
import axios from "axios";

const API = "http://127.0.0.1:5000/api"; // رابط الـ API بتاعك

const axiosInstance = axios.create({
  baseURL: API,
  headers: {
    "Content-Type": "application/json"
  }
});

// interceptor لإضافة الـ JWT لكل request تلقائيًا
axiosInstance.interceptors.request.use(config => {
  const token = localStorage.getItem("token"); // تخزين التوكن بعد تسجيل الدخول
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});

export default axiosInstance;
