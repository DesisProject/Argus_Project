import { useRouteError, Link } from "react-router";

export function ErrorBoundary() {
  const error = useRouteError() as any;

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">⚠️</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">
          Oops! Something went wrong
        </h1>
        <p className="text-slate-600 mb-6">
          {error?.statusText || error?.message || "An unexpected error occurred"}
        </p>
        <Link
          to="/"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
        >
          Go to Home
        </Link>
      </div>
    </div>
  );
}
