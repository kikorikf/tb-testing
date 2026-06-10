import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080/auth",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "tb-realm",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "tb-testing-app",
});

export default keycloak;
