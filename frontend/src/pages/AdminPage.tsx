import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme } from '../types';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import {
  ShieldCheck,
  Edit3,
  History,
  MessageSquare,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Lock
} from 'lucide-react';

export const AdminPage: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [newStatus, setNewStatus] = useState<string>('verified');
  const [newUrl, setNewUrl] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated || user?.role !== 'admin') {
        navigate('/login');
      }
    }
  }, [authLoading, isAuthenticated, user, navigate]);

  const loadAdminData = async () => {
    setIsLoading(true);
    try {
      const [scs, logs] = await Promise.all([
        api.adminGetSchemes(),
        api.adminGetAuditLogs()
      ]);
      setSchemes(scs);
      setAuditLogs(logs);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      loadAdminData();
    }
  }, [user]);

  const handleOpenEdit = (sc: Scheme) => {
    setSelectedScheme(sc);
    setNewStatus(sc.verification_status);
    setNewUrl(sc.official_portal_url);
    setNotes('');
  };

  const handleSaveVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedScheme) return;
    try {
      await api.adminVerifyScheme(selectedScheme.id, {
        verification_status: newStatus,
        official_portal_url: newUrl,
        notes: notes
      });
      setMessage(`Verification status updated for ${selectedScheme.name}`);
      setSelectedScheme(null);
      loadAdminData();
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      alert('Error updating verification: ' + err.message);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-leaf-700 border-t-transparent rounded-full mx-auto" />
        <p className="text-sm text-navy-700/70 mt-3 font-medium">Loading Administrator Verification Portal...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 text-amber-900 text-xs font-bold border border-amber-200">
            <Lock className="w-3.5 h-3.5" />
            <span>Nodal Officer Verification Console</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
            Scheme Provenance & Verification Management
          </h1>
        </div>
      </div>

      {message && <Alert type="success">{message}</Alert>}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left: Scheme Verification Table (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <Card className="p-6 space-y-4">
            <h3 className="font-bold text-base text-navy-900">
              Verified Schemes Catalogue ({schemes.length})
            </h3>

            <div className="space-y-3">
              {schemes.map((sc) => (
                <div
                  key={sc.id}
                  className="p-4 rounded-xl border border-ivory-200 bg-ivory-50/40 flex items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-navy-900">{sc.name}</span>
                      <Badge
                        variant={sc.verification_status === 'verified' ? 'verified' : 'neutral'}
                        size="sm"
                      >
                        {sc.verification_status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xs text-navy-700/70">
                      Dept: {sc.department} • Last Checked: {new Date(sc.last_verified_at).toLocaleDateString()}
                    </p>
                    <a
                      href={sc.official_portal_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-leaf-700 hover:underline flex items-center gap-1"
                    >
                      <span>{sc.official_portal_url}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenEdit(sc)}
                    leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                  >
                    Verify / Edit
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right: Audit Logs (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="p-5 space-y-3">
            <h4 className="font-bold text-sm text-navy-900 flex items-center gap-2">
              <History className="w-4 h-4 text-leaf-700" />
              <span>Administrative Audit Trail</span>
            </h4>
            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {auditLogs.length === 0 ? (
                <p className="text-xs text-navy-700/60 italic">No modifications logged yet.</p>
              ) : (
                auditLogs.map((log) => (
                  <div key={log.id} className="p-2.5 rounded-lg bg-ivory-50 border border-ivory-200 text-xs space-y-1">
                    <span className="font-bold text-navy-900">{log.action}</span>
                    <p className="text-[11px] text-navy-700/70">
                      Target: {log.target_type} #{log.target_id}
                    </p>
                    <span className="text-[10px] text-navy-500 block">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

      </div>

      {/* Edit Scheme Verification Modal */}
      {selectedScheme && (
        <div className="fixed inset-0 z-50 bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-lg w-full p-6 space-y-4 bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <h3 className="font-bold text-base text-navy-900">
                Update Scheme Verification: {selectedScheme.name}
              </h3>
              <button
                onClick={() => setSelectedScheme(null)}
                className="text-navy-500 hover:text-navy-900 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveVerification} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Verification Status
                </label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                >
                  <option value="verified">Verified (Official Active)</option>
                  <option value="under_review">Under Review / Guidelines Updating</option>
                  <option value="deprecated">Deprecated / Discontinued</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Official Portal URL
                </label>
                <input
                  type="url"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Verification Notes / Source Gazette Reference
                </label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Verified against MoRD notification dated 2026-03-01"
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedScheme(null)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Save Verification
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

    </div>
  );
};
