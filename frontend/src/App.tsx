import { useState } from "react";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";

const TOKEN_STORAGE_KEY = "acme_token";

function App() {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY),
  );

  function handleLogin(newToken: string) {
    localStorage.setItem(TOKEN_STORAGE_KEY, newToken);
    setToken(newToken);
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
  }

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }
  return <Dashboard token={token} onLogout={handleLogout} />;
}

export default App;
