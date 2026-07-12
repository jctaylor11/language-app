import { createContext, useContext, useState, useMemo, useEffect } from "react";
import type { ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { checkAuth, logoutUser } from "./api";

interface AuthContextValue {
  isAuthenticated: boolean | null;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  // Need to explicitly request the access_token using http request since its in httpOnly cookie
  useEffect(() => {
    // Defined here so we can use async
    async function checkAuthStatus() {
      const authenticated = await checkAuth().catch(() => false); // Returns false it caught so isAuthenticated isn't stuck on null
      setIsAuthenticated(authenticated);
    }
    checkAuthStatus();
  }, []);

  const login = () => {
    setIsAuthenticated(true); // Source of truth for auth state - influences navbar etc
    queryClient.clear(); // So that everything gets refetched now under new auth state (vocab, sentences, etc)
  };

  const logout = () => {
    logoutUser().catch((error) => console.error("Logout failed:", error)); // Not awaited - More responsiveness, failure unlikely, and not sensitive
    setIsAuthenticated(false);
    queryClient.clear();
  };

  const value = useMemo(
    () => ({ isAuthenticated, login, logout }),
    [isAuthenticated],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
