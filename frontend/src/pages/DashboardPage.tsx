import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import {
  Bookmark,
  FileText,
  AlertCircle,
  FileCheck2,
  Trash2,
  Download,
  Settings,
  User as UserIcon,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading: authLoading, deleteAccount, updateProfile } = useAuth();
  const { currentLanguage, setLanguage } = useLanguage();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'saved' | 'apps' | 'rti' | 'grievances' | 'history' | 'settings'>('saved');
  const [stats, setStats] = useState<any>(null);
  const [savedSchemes, setSavedSchemes] = useState<any[]>([]);
  const [appDrafts, setAppDrafts] = useState<any[]>([]);
  const [rtiDrafts, setRtiDrafts] = useState<any[]>([]);
  const [grievanceDrafts, setGrievanceDrafts] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [authLoading, isAuthenticated, navigate]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [statsData, savedData, appsData, rtiData, grievData, histData] = await Promise.all([
        api.getDashboardStats(),
        api.getSavedSchemes(),
        api.getApplicationDrafts(),
        api.getRtiDrafts(),
        api.getGrievanceDrafts(),
        api.getAssessmentHistory(),
      ]);
      setStats(statsData);
      setSavedSchemes(savedData);
      setAppDrafts(appsData);
      setRtiDrafts(rtiData);
      setGrievanceDrafts(grievData);
      setHistory(histData);
    } catch (err) {
      console.error('Error loading citizen dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData();
    }
  }, [isAuthenticated]);

  const handleRemoveSaved = async (schemeId: number) => {
    await api.toggleSaveScheme(schemeId);
    setSavedSchemes(savedSchemes.filter((s) => s.scheme_id !== schemeId));
  };

  const handleDeleteAppDraft = async (id: number) => {
    if (confirm('Are you sure you want to delete this application draft?')) {
      await api.deleteApplicationDraft(id);
      setAppDrafts(appDrafts.filter((d) => d.id !== id));
    }
  };

  const handleDeleteRtiDraft = async (id: number) => {
    if (confirm('Are you sure you want to delete this RTI draft?')) {
      await api.deleteRtiDraft(id);
      setRtiDrafts(rtiDrafts.filter((d) => d.id !== id));
    }
  };

  const handleDeleteGrievanceDraft = async (id: number) => {
    if (confirm('Are you sure you want to delete this grievance draft?')) {
      await api.deleteGrievanceDraft(id);
      setGrievanceDrafts(grievanceDrafts.filter((d) => d.id !== id));
    }
  };

  const handleDownloadAppPdf = async (id: number) => {
    try {
      const blob = await api.downloadApplicationPdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Application_Draft_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDownloadRtiPdf = async (id: number) => {
    try {
      const blob = await api.downloadRtiPdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `RTI_Petition_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDownloadGrievancePdf = async (id: number) => {
    try {
      const blob = await api.downloadGrievancePdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Grievance_Petition_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleDeleteAccountConfirm = async () => {
    try {
      await deleteAccount();
      alert('Your account and all associated records have been permanently erased from JanSahayak.');
      navigate('/');
    } catch (e: any) {
      alert('Error deleting account: ' + e.message);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-leaf-700 border-t-transparent rounded-full mx-auto" />
        <p className="text-sm text-navy-700/70 mt-3 font-medium">Loading Citizen Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Welcome Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-navy-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-civic">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-navy-800 text-saffron-500 text-xs font-bold">
            <UserIcon className="w-3.5 h-3.5" />
            <span>Citizen Portal</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome, {user?.full_name}
          </h1>
          <p className="text-xs sm:text-sm text-navy-200/80">
            {user?.email} • State: {user?.state || 'Not specified'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/schemes">
            <Button variant="primary" size="sm">
              Discover New Schemes
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card
          onClick={() => setActiveTab('saved')}
          className={`p-4 cursor-pointer text-center space-y-1 transition-all ${
            activeTab === 'saved' ? 'border-leaf-600 bg-leaf-50/30' : ''
          }`}
        >
          <span className="text-2xl font-black text-navy-900">{stats?.saved_schemes_count || 0}</span>
          <p className="text-xs font-bold text-navy-700/70">Saved Schemes</p>
        </Card>

        <Card
          onClick={() => setActiveTab('apps')}
          className={`p-4 cursor-pointer text-center space-y-1 transition-all ${
            activeTab === 'apps' ? 'border-leaf-600 bg-leaf-50/30' : ''
          }`}
        >
          <span className="text-2xl font-black text-navy-900">{stats?.application_drafts_count || 0}</span>
          <p className="text-xs font-bold text-navy-700/70">Application Drafts</p>
        </Card>

        <Card
          onClick={() => setActiveTab('rti')}
          className={`p-4 cursor-pointer text-center space-y-1 transition-all ${
            activeTab === 'rti' ? 'border-leaf-600 bg-leaf-50/30' : ''
          }`}
        >
          <span className="text-2xl font-black text-navy-900">{stats?.rti_drafts_count || 0}</span>
          <p className="text-xs font-bold text-navy-700/70">RTI Drafts</p>
        </Card>

        <Card
          onClick={() => setActiveTab('grievances')}
          className={`p-4 cursor-pointer text-center space-y-1 transition-all ${
            activeTab === 'grievances' ? 'border-leaf-600 bg-leaf-50/30' : ''
          }`}
        >
          <span className="text-2xl font-black text-navy-900">{stats?.grievance_drafts_count || 0}</span>
          <p className="text-xs font-bold text-navy-700/70">Public Grievances</p>
        </Card>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-ivory-200 pb-2 overflow-x-auto text-xs sm:text-sm font-semibold">
        <button
          onClick={() => setActiveTab('saved')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'saved' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          Saved Schemes ({savedSchemes.length})
        </button>
        <button
          onClick={() => setActiveTab('apps')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'apps' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          Application Drafts ({appDrafts.length})
        </button>
        <button
          onClick={() => setActiveTab('rti')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'rti' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          RTI Drafts ({rtiDrafts.length})
        </button>
        <button
          onClick={() => setActiveTab('grievances')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'grievances' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          Grievances ({grievanceDrafts.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'history' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          Assessment History ({history.length})
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 rounded-xl transition-colors whitespace-nowrap ${
            activeTab === 'settings' ? 'bg-navy-900 text-white' : 'text-navy-700 hover:bg-ivory-100'
          }`}
        >
          Settings & Privacy
        </button>
      </div>

      {/* Tab 1: Saved Schemes */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {savedSchemes.length === 0 ? (
            <Card className="p-10 text-center space-y-3">
              <Bookmark className="w-8 h-8 text-navy-400 mx-auto" />
              <p className="font-bold text-navy-900">No saved schemes yet.</p>
              <Link to="/schemes">
                <Button variant="outline" size="sm">Browse Verified Schemes</Button>
              </Link>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedSchemes.map((s) => (
                <Card key={s.saved_id} className="p-5 flex flex-col justify-between">
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold uppercase text-leaf-700">
                      {s.category}
                    </span>
                    <h3 className="font-bold text-base text-navy-900">{s.name}</h3>
                    <p className="text-xs text-navy-700/80 line-clamp-2">{s.summary}</p>
                  </div>
                  <div className="pt-4 border-t border-ivory-200 mt-4 flex items-center justify-between">
                    <Link
                      to={`/eligibility?scheme=${s.slug}`}
                      className="text-xs font-bold text-leaf-700 hover:underline"
                    >
                      Check Eligibility
                    </Link>
                    <button
                      onClick={() => handleRemoveSaved(s.scheme_id)}
                      className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1 font-semibold"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Remove</span>
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Application Drafts */}
      {activeTab === 'apps' && (
        <div className="space-y-4">
          {appDrafts.length === 0 ? (
            <Card className="p-10 text-center space-y-3">
              <FileText className="w-8 h-8 text-navy-400 mx-auto" />
              <p className="font-bold text-navy-900">No application drafts prepared yet.</p>
              <Link to="/applications">
                <Button variant="outline" size="sm">Start Application Prep</Button>
              </Link>
            </Card>
          ) : (
            <div className="space-y-3">
              {appDrafts.map((draft) => (
                <Card key={draft.id} className="p-5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <h4 className="font-bold text-base text-navy-900">{draft.title}</h4>
                    <p className="text-xs text-navy-700/70">
                      Last Updated: {new Date(draft.updated_at).toLocaleDateString()}
                    </p>
                    {draft.notes && (
                      <p className="text-xs text-navy-800 italic">Notes: {draft.notes}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownloadAppPdf(draft.id)}
                      leftIcon={<Download className="w-3.5 h-3.5" />}
                    >
                      PDF
                    </Button>
                    <button
                      onClick={() => handleDeleteAppDraft(draft.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete Draft"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: RTI Drafts */}
      {activeTab === 'rti' && (
        <div className="space-y-4">
          {rtiDrafts.length === 0 ? (
            <Card className="p-10 text-center space-y-3">
              <FileText className="w-8 h-8 text-navy-400 mx-auto" />
              <p className="font-bold text-navy-900">No RTI petitions prepared yet.</p>
              <Link to="/rti">
                <Button variant="outline" size="sm">Draft New RTI Request</Button>
              </Link>
            </Card>
          ) : (
            <div className="space-y-3">
              {rtiDrafts.map((draft) => (
                <Card key={draft.id} className="p-5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <h4 className="font-bold text-base text-navy-900">{draft.subject}</h4>
                    <p className="text-xs text-navy-700/70">
                      Authority: <b>{draft.public_authority}</b> • Date: {new Date(draft.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownloadRtiPdf(draft.id)}
                      leftIcon={<Download className="w-3.5 h-3.5" />}
                    >
                      PDF
                    </Button>
                    <button
                      onClick={() => handleDeleteRtiDraft(draft.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete RTI"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Grievances */}
      {activeTab === 'grievances' && (
        <div className="space-y-4">
          {grievanceDrafts.length === 0 ? (
            <Card className="p-10 text-center space-y-3">
              <AlertCircle className="w-8 h-8 text-navy-400 mx-auto" />
              <p className="font-bold text-navy-900">No public grievances prepared yet.</p>
              <Link to="/grievances">
                <Button variant="outline" size="sm">Draft Grievance</Button>
              </Link>
            </Card>
          ) : (
            <div className="space-y-3">
              {grievanceDrafts.map((draft) => (
                <Card key={draft.id} className="p-5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <h4 className="font-bold text-base text-navy-900">{draft.category}</h4>
                    <p className="text-xs text-navy-700/70">
                      Dept: <b>{draft.department}</b> • {new Date(draft.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleDownloadGrievancePdf(draft.id)}
                      leftIcon={<Download className="w-3.5 h-3.5" />}
                    >
                      PDF
                    </Button>
                    <button
                      onClick={() => handleDeleteGrievanceDraft(draft.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete Grievance"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Assessment History */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {history.length === 0 ? (
            <Card className="p-10 text-center space-y-3">
              <FileCheck2 className="w-8 h-8 text-navy-400 mx-auto" />
              <p className="font-bold text-navy-900">No eligibility assessments on record.</p>
              <Link to="/eligibility">
                <Button variant="outline" size="sm">Run Assessment</Button>
              </Link>
            </Card>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <Card key={item.id} className="p-4 flex items-center justify-between gap-4">
                  <div>
                    <h4 className="font-bold text-sm text-navy-900">{item.scheme_name}</h4>
                    <p className="text-xs text-navy-700/60">
                      Evaluated on: {new Date(item.assessed_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={item.status} size="sm">
                      {item.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                    <Link
                      to={`/eligibility?scheme=${item.scheme_slug}`}
                      className="text-xs font-bold text-leaf-700 hover:underline"
                    >
                      Re-evaluate
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Settings & Privacy Rights */}
      {activeTab === 'settings' && (
        <Card className="p-6 space-y-6">
          <div className="space-y-1">
            <h3 className="font-bold text-lg text-navy-900">Citizen Settings & Privacy Rights</h3>
            <p className="text-xs text-navy-700/70">
              Update preferences or exercise your statutory data privacy rights.
            </p>
          </div>

          <div className="max-w-md space-y-4">
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Preferred Interface Language
              </label>
              <select
                value={currentLanguage}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="bn">বাংলা (Bengali)</option>
                <option value="ta">தமிழ் (Tamil)</option>
                <option value="te">తెలుగు (Telugu)</option>
                <option value="mr">मराठी (Marathi)</option>
                <option value="gu">ગુજરાતી (Gujarati)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
                <option value="ml">മലയാളം (Malayalam)</option>
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="or">ଓଡ଼ିଆ (Odia)</option>
              </select>
            </div>
          </div>

          {/* Account Deletion / Data Rights Section */}
          <div className="pt-6 border-t border-ivory-200 space-y-3">
            <h4 className="text-sm font-bold text-red-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span>Right to Erasure (Account & Data Deletion)</span>
            </h4>
            <p className="text-xs text-navy-700/80 leading-relaxed">
              In accordance with our Privacy Charter, you may permanently erase your account, login credentials, and all drafts (applications, RTIs, grievances) from our database with immediate effect.
            </p>
            <div>
              <Button
                variant="danger"
                size="sm"
                onClick={() => setDeleteConfirmOpen(true)}
              >
                Permanently Delete My Citizen Account
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmOpen && (
        <div className="fixed inset-0 z-50 bg-navy-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4 bg-white shadow-2xl">
            <div className="flex items-center gap-2 text-red-700 font-bold text-base">
              <ShieldAlert className="w-5 h-5 shrink-0" />
              <span>Confirm Account Deletion</span>
            </div>
            <p className="text-xs text-navy-800 leading-relaxed">
              This action is permanent and cannot be undone. All saved schemes, drafts, and assessment history associated with <b>{user?.email}</b> will be completely purged from JanSahayak.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeleteConfirmOpen(false)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteAccountConfirm}
              >
                Yes, Delete Everything
              </Button>
            </div>
          </Card>
        </div>
      )}

    </div>
  );
};
