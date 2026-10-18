import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await login({ email, password });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickDemoLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16 space-y-6">
      
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-navy-900 text-white flex items-center justify-center mx-auto text-xl font-extrabold shadow-sm">
          जन
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
          Citizen Portal Login
        </h1>
        <p className="text-xs sm:text-sm text-navy-700/70">
          Access your saved schemes, application drafts, and RTI requests.
        </p>
      </div>

      <Card className="p-6 sm:p-8 space-y-6">
        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-navy-400 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="citizen@example.com"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-navy-400 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full"
          >
            Sign In to Citizen Dashboard
          </Button>
        </form>

        {/* Demo Quick Login Assistant */}
        <div className="p-3.5 rounded-xl bg-ivory-50 border border-ivory-200 space-y-2 text-xs">
          <span className="font-bold text-navy-900 flex items-center gap-1.5">
            <UserCheck className="w-4 h-4 text-saffron-600" />
            <span>Developer / Reviewer Quick Fill:</span>
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemoLogin('admin@jansahayak.gov.in', 'JanSahayakAdmin@2026')}
              className="px-2.5 py-1 rounded-lg bg-white border border-ivory-300 hover:border-leaf-500 font-semibold text-navy-800 text-[11px]"
            >
              Fill Admin Officer
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-navy-700/80 pt-2 border-t border-ivory-200">
          New citizen?{' '}
          <Link to="/register" className="font-bold text-leaf-700 hover:underline">
            Create Free Account
          </Link>
        </div>
      </Card>

    </div>
  );
};
