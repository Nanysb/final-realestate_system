// 4. admin-dashboard/src/api.js - الإصدار المصحح
import axios from "axios";

const API_BASE_URL = "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("admin_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && 
        !originalRequest._retry && 
        !originalRequest.url.includes('/auth/')) {
      
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);  // ✅ الإصلاح هنا
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem("admin_refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token");
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
          headers: {
            'Authorization': `Bearer ${refreshToken}`
          }
        });

        if (response.data.ok) {
          const newAccessToken = response.data.access_token;
          localStorage.setItem("admin_token", newAccessToken);
          
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          processQueue(null, newAccessToken);
          
          return api(originalRequest);  // ✅ الإصلاح هنا
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_refresh_token");
        localStorage.removeItem("user_data");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const loginAdmin = async (username, password) => {
  try {
    const response = await api.post("/auth/login", {
      username,
      password
    });
    
    if (response.data.ok) {
      localStorage.setItem("admin_token", response.data.access_token);
      localStorage.setItem("admin_refresh_token", response.data.refresh_token);
      localStorage.setItem("user_data", JSON.stringify(response.data.user));
    }
    return response.data;
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
};

export const verifyToken = async () => {
  try {
    const response = await api.get("/auth/verify");
    return response.data;
  } catch (error) {
    console.error("Token verification error:", error);
    return { ok: false, error: "Token invalid" };
  }
};

export const logoutAdmin = async () => {
  try {
    await api.post("/auth/logout");
  } catch (error) {
    console.warn("Logout API call failed, clearing tokens locally");
  } finally {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_refresh_token");
    localStorage.removeItem("user_data");
    window.location.href = "/login";
  }
};

export const getCompanies = async () => {
  try {
    const response = await api.get("/companies");
    return response.data;
  } catch (error) {
    console.error("Get companies error:", error);
    throw error;
  }
};

export const createCompany = async (companyData) => {
  try {
    const response = await api.post("/companies", companyData);
    return response.data;
  } catch (error) {
    console.error("Create company error:", error);
    throw error;
  }
};

export const updateCompany = async (id, companyData) => {
  try {
    const response = await api.put(`/companies/${id}`, companyData);
    return response.data;
  } catch (error) {
    console.error("Update company error:", error);
    throw error;
  }
};

export const deleteCompany = async (id) => {
  try {
    const response = await api.delete(`/companies/${id}`);
    return response.data;
  } catch (error) {
    console.error("Delete company error:", error);
    throw error;
  }
};

export const getProjects = async (params = {}) => {
  try {
    const response = await api.get("/projects", { params });
    return response.data;
  } catch (error) {
    console.error("Get projects error:", error);
    throw error;
  }
};

export const getProject = async (id) => {
  try {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  } catch (error) {
    console.error("Get project error:", error);
    throw error;
  }
};

export const createProject = async (projectData) => {
  try {
    const response = await api.post("/projects", projectData);
    return response.data;
  } catch (error) {
    console.error("Create project error:", error);
    throw error;
  }
};

export const updateProject = async (id, projectData) => {
  try {
    const response = await api.put(`/projects/${id}`, projectData);
    return response.data;
  } catch (error) {
    console.error("Update project error:", error);
    throw error;
  }
};

export const deleteProject = async (id) => {
  try {
    const response = await api.delete(`/projects/${id}`);
    return response.data;
  } catch (error) {
    console.error("Delete project error:", error);
    throw error;
  }
};

export const getUnits = async (params = {}) => {
  try {
    const response = await api.get("/units", { params });
    return response.data;
  } catch (error) {
    console.error("Get units error:", error);
    throw error;
  }
};

export const getUnit = async (id) => {
  try {
    const response = await api.get(`/units/${id}`);
    return response.data;
  } catch (error) {
    console.error("Get unit error:", error);
    throw error;
  }
};

export const createUnit = async (unitData) => {
  try {
    const response = await api.post("/units", unitData);
    return response.data;
  } catch (error) {
    console.error("Create unit error:", error);
    throw error;
  }
};

export const updateUnit = async (id, unitData) => {
  try {
    const response = await api.put(`/units/${id}`, unitData);
    return response.data;
  } catch (error) {
    console.error("Update unit error:", error);
    throw error;
  }
};

export const deleteUnit = async (id) => {
  try {
    const response = await api.delete(`/units/${id}`);
    return response.data;
  } catch (error) {
    console.error("Delete unit error:", error);
    throw error;
  }
};

export const uploadFile = async (fileData) => {
  try {
    const response = await api.post("/upload", fileData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error("Upload file error:", error);
    throw error;
  }
};

export const uploadProjectImages = async (projectId, images) => {
  try {
    const formData = new FormData();
    images.forEach(image => {
      formData.append('images', image);
    });
    
    const response = await api.post(`/projects/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error("Upload project images error:", error);
    throw error;
  }
};

export const uploadUnitFiles = async (unitId, files) => {
  try {
    const formData = new FormData();
    if (files.images) {
      files.images.forEach(image => {
        formData.append('images', image);
      });
    }
    if (files.floor_plan) {
      formData.append('floor_plan', files.floor_plan);
    }
    
    const response = await api.post(`/units/${unitId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error("Upload unit files error:", error);
    throw error;
  }
};

export const getCurrentUser = () => {
  const userData = localStorage.getItem("user_data");
  return userData ? JSON.parse(userData) : null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem("admin_token");
};

export const getAuthHeaders = () => {
  const token = localStorage.getItem("admin_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default api;

