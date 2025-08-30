import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000/api"; // تأكد إنه نفس الـ Flask API

// إضافة JWT Token للأدمن
let token = localStorage.getItem("admin_token") || null;

const headers = () => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});

export const loginAdmin = async (username, password) => {
  const res = await axios.post(`${API_BASE_URL}/auth/login`, { username, password });
  if(res.data.ok) {
    token = res.data.access_token;
    localStorage.setItem("admin_token", token);
  }
  return res.data;
};

export const getCompanies = async () => {
  const res = await axios.get(`${API_BASE_URL}/companies`, { headers: headers() });
  return res.data;
};

export const createCompany = async (slug, name) => {
  const res = await axios.post(`${API_BASE_URL}/companies`, { slug, name }, { headers: headers() });
  return res.data;
};

// وهكذا لكل العمليات: Projects, Units, تعديل وحذف
