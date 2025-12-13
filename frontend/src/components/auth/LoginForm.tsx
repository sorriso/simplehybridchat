/* path: frontend/src/components/auth/LoginForm.tsx
   version: 6 - FIXED: Accept error as string | null | undefined for TypeScript compatibility */

"use client";

import { useState } from "react";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

interface LoginFormProps {
  onLogin: (email: string, password: string) => Promise<any>;
  loading?: boolean;
  error?: string | null;
}

export function LoginForm({ onLogin, loading, error }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError("");

    if (!email.trim()) {
      setLocalError("Email is required");
      return;
    }
    if (!password.trim()) {
      setLocalError("Password is required");
      return;
    }

    try {
      await onLogin(email, password);
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  const displayError = error || localError;

  return (
    <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg">
      <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          type="email"
          label="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          disabled={loading}
          autoFocus
        />
        <Input
          type="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          disabled={loading}
        />
        {displayError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{displayError}</p>
          </div>
        )}
        <Button type="submit" fullWidth disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
}
