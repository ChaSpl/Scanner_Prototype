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
  status: string;
}

interface Viz {
  id: number;
  type: string;      // e.g. "pdf" or "timeline"
  file_path: string; // starts with "/pdfs/..." or "/static/..."
}

export default function Dashboard() {
  const auth = useContext(AuthContext)!;
  const navigate = useNavigate();

  const [user, setUser] = useState<MeResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [docId, setDocId] = useState<number | null>(null);
  const [docStatus, setDocStatus] = useState<string | null>(null);
  const [visualizations, setVisualizations] = useState<Viz[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1) load current user
  useEffect(() => {
    if (!auth.token) {
      navigate('/login');
      return;
    }
    api.get<MeResponse>('/me')
      .then(res => setUser(res.data))
      .catch(() => {
        setError('Failed to load profile.');
        auth.logout();
        navigate('/login');
      });
  }, [auth, navigate]);

  // 2) poll document status
  useEffect(() => {
    if (!docId) return;
    setUploading(true);
    const interval = setInterval(() => {
      api.get<DocumentStatus>(`/documents/${docId}`)
        .then(res => {
          const st = res.data.status;
          setDocStatus(st);
          setError(null);
          if (st === 'parsed' || st === 'complete') {
            clearInterval(interval);
          }
        })
        .catch(err => {
          console.error('Status poll failed', err);
          setError('Failed to fetch document status.');
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [docId]);

  // 3) poll for visualizations when parsed or complete
  useEffect(() => {
    if (!docId || (docStatus !== 'parsed' && docStatus !== 'complete')) return;
    const interval = setInterval(() => {
      api.get<Viz[]>(`/documents/${docId}/visualizations`)
        .then(res => {
          if (res.data.length > 0) {
            setVisualizations(res.data);
            clearInterval(interval);
            setUploading(false);
          }
        })
        .catch(() => {
          // swallow—will try again
        });
    }, 2000);
    return () => clearInterval(interval);
  }, [docId, docStatus]);

  // 4) stop spinner if status flips to complete before viz arrive
  useEffect(() => {
    if (docStatus === 'complete') {
      setUploading(false);
    }
  }, [docStatus]);

  // file picker
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
  };

  // upload action
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadStatus(null);
    setError(null);
    setDocId(null);
    setDocStatus(null);
    setVisualizations([]);

    try {
      const form = new FormData();
      form.append('file', file);
      const res = await api.post<UploadResponse>('/documents/upload', form);
      setDocId(res.data.document_id);
      setUploadStatus(`Uploaded: doc #${res.data.document_id}`);
    } catch (err: any) {
      console.error('Upload error', err);
      setError(err.response?.data?.detail || 'Upload failed.');
      setUploading(false);
    }
  };

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
            ? <span className="animate-spin flex items-center gap-2">✒️ Processing…</span>
            : 'Upload'}
        </button>
        {uploadStatus && <p className="mt-2 text-green-600">{uploadStatus}</p>}
        {docStatus && <p className="mt-1 text-blue-600">Status: {docStatus}</p>}
        {error && <p className="mt-2 text-red-600">{error}</p>}
      </section>

      {/* Artifacts Section */}
      {visualizations.length > 0 && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-2">Your Files</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {visualizations.map(v => (
              <div key={v.id} className="border p-4 flex flex-col items-start">
                <p className="text-sm font-medium mb-2 capitalize">{v.type}</p>

                {/* Timeline image */}
                {v.type === 'timeline' && (
                  <img
                    src={v.file_path}
                    alt="Timeline"
                    className="w-full h-auto mb-2"
                  />
                )}

                {/* PDF download */}
                {v.type === 'pdf' && (
                  <p className="mb-2 text-sm text-gray-600">Your CV PDF is ready</p>
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
