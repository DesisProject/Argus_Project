import { RouterProvider } from 'react-router';
import { router } from './routes';
import { useState, useEffect } from 'react';
import { LoginForm } from './components/LoginForm'; 
import { getToken, logoutUser } from './services/auth'; 

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // When the app starts, check if they already have a ticket saved
    const token = getToken();
    if (token) {
      setIsAuthenticated(true);
    }
    setIsLoading(false); // Finished checking
  }, []);

  // Show a simple loading state while checking for the token
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Argus...</div>;
  }

  // If no ticket, block the router and show the login form
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <LoginForm onLoginSuccess={() => setIsAuthenticated(true)} />
      </div>
    );
  }

  // If they have a ticket, load the router (the actual Argus application)
  return (
    <div className="relative">
      {/* A floating logout button so you can test logging in and out */}
      <button
        onClick={() => {
          logoutUser();
          setIsAuthenticated(false);
        }}
        className="absolute top-4 right-4 z-50 bg-red-500 text-white px-4 py-2 rounded shadow hover:bg-red-600 transition"
      >
        Log Out
      </button>
      
      <RouterProvider router={router} />
    </div>
  );
}
