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
  type: string;
  file_path: string;
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

  // load current user
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
  }, [auth.token, navigate]);

  // poll document status until parsed
  useEffect(() => {
  if (!docId) return;
  const interval = setInterval(() => {
    api.get<DocumentStatus>(`/documents/${docId}`)
      .then(res => {
        const st = res.data.status;
        setDocStatus(st);
        setError(null);                 // clear any old error

        // stop polling as soon as we hit either parsed or complete
        if (st === 'parsed' || st === 'complete') {
          clearInterval(interval);
        }
      })
      .catch(err => {
        console.error('Status poll failed', err);
        // keep retrying—but show the error
        setError('Failed to fetch document status.');
        // don't clearInterval here, so we retry automatically
        // if you want a backoff, you could clear+restart
      });
  }, 2000);
  return () => clearInterval(interval);
}, [docId]);

  // poll for visualizations once parsed
  useEffect(() => {
    if (!docId || docStatus !== 'parsed') return;
    const interval = setInterval(() => {
      api.get<Viz[]>(`/documents/${docId}/visualizations`)
        .then(res => {
          if (res.data.length) {
            setVisualizations(res.data);
            clearInterval(interval);
            setUploading(false);
          }
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [docId, docStatus]);

  useEffect(() => {
    if (docStatus === 'parsed' || docStatus === 'complete') {
      setUploading(false);
    }
  }, [docStatus]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    console.log('📁 File selected:', selected);
    setFile(selected);
  };

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
      const id = res.data.document_id;
      setDocId(id);
      setUploadStatus(`Uploaded: doc #${id}`);
    } catch (err: any) {
      console.error('❌ Upload error', err);
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

      {/* Timeline Preview Section */}
      {visualizations.length > 0 && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-2">Your Timeline</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {visualizations.map(v => (
              <div key={v.id} className="border p-2">
                <p className="text-sm font-medium mb-1">{v.type}</p>
                <img
                  src={`${import.meta.env.VITE_API_URL}/${v.file_path}`}
                  alt={v.type}
                  className="w-full h-auto"
                />
                <a
                  href={`${import.meta.env.VITE_API_URL}/${v.file_path}`}
                  download
                  className="mt-2 inline-block text-blue-600 hover:underline"
                >
                  Download
                </a>
              </div>
            ))}
          </div>
        </section>
      )}

      <button
        onClick={() => {
          auth.logout();
          navigate('/login');
        }}
        className="btn-secondary mt-6"
      >
        Log Out
      </button>
    </main>
  );
}
