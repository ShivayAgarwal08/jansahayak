import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Lock, Mail, User, MapPin, Phone, ShieldCheck } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    phone: '',
    state: 'Uttar Pradesh',
    preferred_language: 'en'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await register(formData);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check the form.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12 sm:py-16 space-y-6">
      
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-leaf-700 text-white flex items-center justify-center mx-auto text-xl font-extrabold shadow-sm">
          जन
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
          Create Citizen Account
        </h1>
        <p className="text-xs sm:text-sm text-navy-700/70">
          Save application drafts, bookmark schemes, and export official reports.
        </p>
      </div>

      <Card className="p-6 sm:p-8 space-y-6">
        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-navy-400 absolute left-3 top-3.5" />
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Ramesh Kumar"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-navy-400 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="ramesh@example.com"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Create Password (min. 6 characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-navy-400 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                minLength={6}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="••••••••"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                State of Residence
              </label>
              <input
                type="text"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Language
              </label>
              <select
                value={formData.preferred_language}
                onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="bn">বাংলা</option>
                <option value="ta">தமிழ்</option>
                <option value="te">తెలుగు</option>
                <option value="mr">मराठी</option>
              </select>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-ivory-50 border border-ivory-200 text-xs text-navy-700 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-leaf-700 shrink-0" />
            <span>Privacy Promise: We never request or store your Aadhaar or bank PIN.</span>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full"
          >
            Register & Continue
          </Button>
        </form>

        <div className="text-center text-xs text-navy-700/80 pt-2 border-t border-ivory-200">
          Already registered?{' '}
          <Link to="/login" className="font-bold text-leaf-700 hover:underline">
            Sign In Here
          </Link>
        </div>
      </Card>

    </div>
  );
};
