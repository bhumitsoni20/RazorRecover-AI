"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { MerchantUser, AuthResponse, VerificationStatus } from "@/types/auth";
import { apiClient } from "@/lib/api-client";

interface AuthContextType {
  user: MerchantUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  signup: (payload: {
    business_name: string;
    owner_name: string;
    email: string;
    password: string;
    confirm_password: string;
    currency?: string;
  }) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<MerchantUser | null>;
  devVerify: (status?: VerificationStatus, notes?: string) => Promise<MerchantUser>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<MerchantUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  const refreshUser = useCallback(async (): Promise<MerchantUser | null> => {
    try {
      const me = await apiClient.getMe();
      setUser(me);
      return me;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    setLoading(true);
    try {
      const res = await apiClient.login({ email, password });
      setUser(res.merchant);
      return res;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (payload: {
    business_name: string;
    owner_name: string;
    email: string;
    password: string;
    confirm_password: string;
    currency?: string;
  }): Promise<AuthResponse> => {
    setLoading(true);
    try {
      const res = await apiClient.signup(payload);
      setUser(res.merchant);
      return res;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setLoading(true);
    try {
      await apiClient.logout();
      setUser(null);
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  const devVerify = async (status: VerificationStatus = "VERIFIED", notes?: string): Promise<MerchantUser> => {
    if (!user) throw new Error("No authenticated merchant found");
    const updated = await apiClient.devVerifyMerchant(user.id, status, notes);
    setUser(updated);
    return updated;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        refreshUser,
        devVerify,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
