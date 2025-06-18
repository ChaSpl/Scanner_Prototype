// src/pages/Dashboard.tsx
// Upon change, run: npm run build in app/frontend terminal

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
  type: string;      // whatever string your backend uses, e.g. "PDF" or "PNG"
  file_path: string; // "/pdfs/..." or "/static/..."
}

export default function Dashboard() {
  const auth = useContext(AuthContext)!;
  const navigate = useNavigate();

  const [user, setUser] = useState<MeResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState(false);
  const [docId, setDocId] = useState<number | null>(null);
  const [docStatus, setDocStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [visualizations, setVisualizations] = useState<Viz[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Load user
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

  // 2. File selection & upload
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

  // 3. Poll status
  useEffect(() => {
    if (!docId) return;
    const iv = setInterval(async () => {
      try {
        const { data } = await api.get<DocumentStatus>(`/documents/${docId}`);
        setDocStatus(data.status);
        if (data.status === 'complete' || data.status === 'error') {
          clearInterval(iv);
          setUploading(false);
        }
      } catch {
        setError('Failed to fetch status.');
      }
    }, 2000);
    return () => clearInterval(iv);
  }, [docId]);

  // 4. Once complete, fetch viz
  useEffect(() => {
    if (docStatus !== 'complete') return;
    const iv = setInterval(async () => {
      try {
        const { data } = await api.get<Viz[]>(`/documents/${docId}/visualizations`);
        if (data.length > 0) {
          setVisualizations(data);
          clearInterval(iv);
        }
      } catch {
        // keep retrying
      }
    }, 2000);
    return () => clearInterval(iv);
  }, [docStatus, docId]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading profile…</p>
      </div>
    );
  }

  // Pick one PDF, one “not-PDF” as timeline:
  const pdfViz = visualizations.find(v => v.type.toLowerCase() === 'pdf');
  const timelineViz = visualizations.find(v => v.type.toLowerCase() !== 'pdf');

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-800">
      <h1 className="text-3xl font-bold mb-4">Welcome, {user.full_name}!</h1>
      <p className="mb-6">Email: {user.email}</p>

      {/* Upload */}
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

      {/* Files */}
      {docStatus === 'complete' && (pdfViz || timelineViz) && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-2">Your Files</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pdfViz && (
              <div className="border p-4 flex flex-col">
                <p className="text-sm font-medium mb-2">PDF</p>
                <p className="mb-2 text-sm text-gray-600">
                  Your parsed CV is ready
                </p>
                <a
                  href={pdfViz.file_path}
                  download
                  className="mt-auto text-blue-600 hover:underline"
                >
                  Download PDF
                </a>
              </div>
            )}
            {timelineViz && (
              <div className="border p-4 flex flex-col">
                <p className="text-sm font-medium mb-2">Timeline</p>
                <img
                  src={timelineViz.file_path}
                  alt="Timeline"
                  className="w-full h-auto mb-2"
                />
                <a
                  href={timelineViz.file_path}
                  download
                  className="mt-auto text-blue-600 hover:underline"
                >
                  Download Timeline
                </a>
              </div>
            )}
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
