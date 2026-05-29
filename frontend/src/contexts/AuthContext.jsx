import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import { clearAuth, getStoredUser, getToken, setStoredUser, setToken } from "../services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    try {
      const profile = await api.me();
      setUser(profile);
      setStoredUser(profile);
      return profile;
    } catch {
      if (!getToken()) {
        setUser(null);
      }
      return null;
    }
  }, []);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await loadUser();
      setLoading(false);
    }
    init();
  }, [loadUser]);

  const login = useCallback(async (payload) => {
    const data = await api.login(payload);
    setToken(data.access_token);
    setUser(data.user);
    setStoredUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (payload) => {
    const data = await api.register(payload);
    setToken(data.access_token);
    setUser(data.user);
    setStoredUser(data.user);
    return data;
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      loadUser,
    }),
    [user, loading, login, register, logout, loadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
