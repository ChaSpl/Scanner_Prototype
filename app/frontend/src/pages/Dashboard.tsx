// src/pages/Dashboard.tsx
import { useContext, useEffect, useState, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

interface MeResponse {
  id: number;
  full_name: string;
  email: string;
}

interface UploadResponse {
  document_id: number;
  status: string;
}

interface DocumentStatus {
  id: number;
  status: 'pending' | 'parsed' | 'complete' | 'error';
}

interface Viz {
  id: number;
  type: string;      // "pdf" or "timeline"
  file_path: string; // "/pdfs/..." or "/static/..."
}

export default function Dashboard() {
  const auth = useContext(AuthContext)!;
  const navigate = useNavigate();

  const [user, setUser] = useState<MeResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);

  // upload + status
  const [uploading, setUploading] = useState(false);
  const [docId, setDocId] = useState<number | null>(null);
  const [docStatus, setDocStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // visualizations
  const [visualizations, setVisualizations] = useState<Viz[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // — 1) Load current user
  useEffect(() => {
    if (!auth.token) {
      navigate('/login');
      return;
    }
    api.get<MeResponse>('/me')
      .then(res => setUser(res.data))
      .catch(() => {
        auth.logout();
        navigate('/login');
      });
  }, [auth, navigate]);

  // — 2) Upload handler
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null);
  };
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setDocId(null);
    setDocStatus(null);
    setVisualizations([]);

    try {
      const form = new FormData();
      form.append('file', file);
      const res = await api.post<UploadResponse>('/documents/upload', form);
      setDocId(res.data.document_id);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Upload failed.');
      setUploading(false);
    }
  };

  // — 3) Poll for status: pending → parsed → complete
  useEffect(() => {
    if (!docId) return;
    const interval = setInterval(async () => {
      try {
        const res = await api.get<DocumentStatus>(`/documents/${docId}`);
        setDocStatus(res.data.status);

        // Stop polling once complete
        if (res.data.status === 'complete' || res.data.status === 'error') {
          clearInterval(interval);
          setUploading(false);
        }
      } catch (err) {
        console.error('Status poll failed', err);
        setError('Failed to fetch status.');
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [docId]);

  // — 4) Once complete, fetch visualizations
  useEffect(() => {
    if (docStatus !== 'complete') return;
    const interval = setInterval(async () => {
      try {
        const res = await api.get<Viz[]>(`/documents/${docId}/visualizations`);
        if (res.data.length > 0) {
          setVisualizations(res.data);
          clearInterval(interval);
        }
      } catch {
        // keep retrying
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [docStatus, docId]);

  // — Redirect if not logged in / not loaded
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading your profile…</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-800">
      <h1 className="text-3xl font-bold mb-4">Welcome, {user.full_name}!</h1>
      <p className="mb-6">Email: {user.email}</p>

      {/* Upload Section */}
      <section className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-semibold mb-2">Upload Your CV</h2>
        <input
          type="file"
          accept=".pdf,.docx"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="flex items-center gap-4 mb-4">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="btn-secondary px-4 py-2"
          >
            Choose File
          </button>
          <span>{file ? file.name : 'No file chosen'}</span>
        </div>
        <button
          onClick={handleUpload}
          disabled={uploading || !file}
          className="btn-primary flex items-center gap-2"
        >
          {uploading
            ? <span className="animate-spin">Processing…</span>
            : 'Upload'}
        </button>
        {docStatus && (
          <p className="mt-2 text-blue-600">
            Status: <strong>{docStatus}</strong>
          </p>
        )}
        {error && <p className="mt-2 text-red-600">{error}</p>}
      </section>

      {/* Visualizations Section */}
      {docStatus === 'complete' && visualizations.length > 0 && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-2">Your Files</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {visualizations.map(v => (
              <div key={v.id} className="border p-4 flex flex-col">
                <p className="text-sm font-medium mb-2 capitalize">{v.type}</p>

                {v.type === 'timeline' && (
                  <img
                    src={v.file_path}
                    alt="Timeline"
                    className="w-full h-auto mb-2"
                  />
                )}

                {v.type === 'pdf' && (
                  <p className="mb-2 text-sm text-gray-600">
                    Your parsed CV (PDF) is ready
                  </p>
                )}

                <a
                  href={v.file_path}
                  download
                  className="mt-auto text-blue-600 hover:underline"
                >
                  Download {v.type === 'timeline' ? 'Timeline' : 'PDF'}
                </a>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Logout */}
      <button
        onClick={() => { auth.logout(); navigate('/login'); }}
        className="btn-secondary mt-6"
      >
        Log Out
      </button>
    </main>
  );
}
