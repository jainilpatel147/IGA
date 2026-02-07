import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/request';

/**
 * Auth Context
 * Manages authentication state and JWT tokens
 */
const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(() => localStorage.getItem('iga-token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing token and validate
        if (token) {
            // Decode token to get user info (demo - in production verify with backend)
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setUser({
                    username: payload.sub,
                    role: payload.role,
                    application_id: payload.application_id,
                    exp: payload.exp
                });
            } catch {
                // Invalid token, clear it
                logout();
            }
        }
        setLoading(false);
    }, [token]);

    const login = async (username, password) => {
        try {
            const data = await api.post('/auth/login', { username, password });

            localStorage.setItem('iga-token', data.access_token);
            setToken(data.access_token);

            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    };

    const logout = () => {
        localStorage.removeItem('iga-token');
        setToken(null);
        setUser(null);
    };

    const isAuthenticated = !!user;

    return (
        <AuthContext.Provider value={{
            user,
            token,
            login,
            logout,
            isAuthenticated,
            loading
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
