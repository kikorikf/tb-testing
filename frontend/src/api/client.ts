import axios from "axios";
import keycloak from "../keycloak";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
});

api.interceptors.request.use(async (config) => {
  if (keycloak.isTokenExpired(30)) {
    await keycloak.updateToken(30);
  }
  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`;
  }
  return config;
});

export default api;
