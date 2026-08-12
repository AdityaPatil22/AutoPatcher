import { useCallback, useState } from "react";
import { getMe, logout as apiLogout } from "../api/auth";
import type { User } from "../types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  function login(backendUrl?: string) {
    const base = backendUrl || "";
    window.location.href = `${base}/api/auth/github`;
  }

  async function logout() {
    try {
      await apiLogout();
    } catch {
      /* ignore */
    }
    setUser(null);
  }

  return {
    user,
    isLoggedIn: !!user,
    loading,
    checkAuth,
    login,
    logout,
  } as const;
}

export type UseAuthReturn = ReturnType<typeof useAuth>;
