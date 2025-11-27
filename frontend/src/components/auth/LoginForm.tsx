/* path: src/components/auth/LoginForm.tsx
   version: 5 - Fixed onLogin type to return Promise<User> and removed icon prop */

import { useState } from "react";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { LogIn } from "lucide-react";
import type { User } from "@/types/auth";

interface LoginFormProps {
  onLogin?: (email: string, password: string) => Promise<User>;
  loading?: boolean;
  error?: string | null;
}

/**
 * Login form for local authentication mode
 */
export function LoginForm({ onLogin, loading, error }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!email.trim()) {
      setLocalError("Email is required");
      return;
    }

    if (!password) {
      setLocalError("Password is required");
      return;
    }

    setLocalError(null);

    try {
      if (onLogin) {
        await onLogin(email, password);
      }
    } catch (err) {
      // Error will be shown via the error prop
      console.error("Login error:", err);
    }
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Log In
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account to continue
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {displayError && (
            <div
              className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded"
              role="alert"
            >
              {displayError}
            </div>
          )}

          <div className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              autoComplete="email"
              disabled={loading}
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            disabled={loading}
          >
            <LogIn className="w-4 h-4 mr-2" />
            {loading ? "Logging in..." : "Log In"}
          </Button>
        </form>

        <div className="text-center text-sm text-gray-600">
          <p>Demo credentials:</p>
          <p className="font-mono text-xs mt-1">admin@example.com / admin123</p>
        </div>
      </div>
    </div>
  );
}
