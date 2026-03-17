import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { loginUser, registerUser } from '../services/auth';

export const LoginForm = () => {
    const navigate = useNavigate();
    const location = useLocation();
    
    const [isLoginMode, setIsLoginMode] = useState(location.pathname !== '/signup'); 
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    useEffect(() => {
        setIsLoginMode(location.pathname !== '/signup');
        setError('');
        setSuccessMsg('');
    }, [location.pathname]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccessMsg('');
        
        try {
            if (isLoginMode) {
                await loginUser(email, password);
                navigate('/dashboard'); 
            } else {
                await registerUser(email, password);
                setSuccessMsg('Account created successfully! You can now sign in.');
                navigate('/login');
                setPassword(''); 
            }
        } catch (err: any) {
            setError(err.message || 'Something went wrong. Please try again.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full p-8 bg-white rounded-xl shadow-lg border border-gray-100">
                <h2 className="text-3xl font-bold mb-6 text-center text-gray-800">
                    {isLoginMode ? 'Argus Login' : 'Create Argus Account'}
                </h2>
                
                {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm text-center">{error}</div>}
                {successMsg && <div className="bg-green-50 text-green-600 p-3 rounded mb-4 text-sm text-center">{successMsg}</div>}
                
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-semibold mb-2">Email</label>
                        <input 
                            type="email" 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                            placeholder="founder@startup.com"
                            required
                        />
                    </div>
                    
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-semibold mb-2">Password</label>
                        <input 
                            type="password" 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    
                    <button 
                        type="submit" 
                        className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 active:bg-blue-800 transition shadow-md"
                    >
                        {isLoginMode ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-gray-600 text-sm">
                        {isLoginMode ? "Don't have an account yet?" : "Already have an account?"}
                        <button 
                            type="button"
                            onClick={() => navigate(isLoginMode ? '/signup' : '/login')}
                            className="ml-2 text-blue-600 font-semibold hover:text-blue-800 hover:underline transition"
                        >
                            {isLoginMode ? 'Sign Up' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};
