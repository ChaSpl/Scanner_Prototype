// src/pages/Landing.tsx
import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800 px-4">
      <div className="w-full max-w-md text-center">
        {/* Page title */}
        <h1 className="text-4xl md:text-5xl font-extrabold mb-2">
          Welcome to Skill Scanner
        </h1>
        {/* Subtitle */}
        <p className="text-lg md:text-xl mb-8">
          Please register or log in to continue.
        </p>
        {/* Buttons */}
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link to="/login" className="btn-primary px-6 py-3">
            Login
          </Link>
          <Link to="/register" className="btn-secondary px-6 py-3">
            Register
          </Link>
        </div>
      </div>
    </main>
  );
}
