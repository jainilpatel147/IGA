import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme, App as AntApp } from 'antd'
import { ThemeProvider, useTheme } from './context/ThemeContext'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Identities from './pages/Identities'
import AccessRequests from './pages/AccessRequests'
import AuditLog from './pages/AuditLog'
import Roles from './pages/Roles'
import Resources from './pages/Resources'
import ApiKeys from './pages/ApiKeys'
import Connectors from './pages/Connectors'
import AccessReviews from './pages/AccessReviews'
import Compliance from './pages/Compliance'
import Applications from './pages/Applications'
import GovernanceEvidence from './pages/GovernanceEvidence'
import MyAccess from './pages/MyAccess'

/**
 * Protected Route Wrapper
 */
function ProtectedRoute({ children }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh'
            }}>
                Loading...
            </div>
        );
    }

    return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/**
 * App Routes
 */
function AppRoutes() {
    const { isAuthenticated } = useAuth();

    return (
        <Routes>
            <Route
                path="/login"
                element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
            />
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Dashboard />} />
                <Route path="identities" element={<Identities />} />
                <Route path="access-requests" element={<AccessRequests />} />
                <Route path="roles" element={<Roles />} />
                <Route path="resources" element={<Resources />} />
                <Route path="audit" element={<AuditLog />} />
                <Route path="api-keys" element={<ApiKeys />} />
                <Route path="connectors" element={<Connectors />} />
                <Route path="access-reviews" element={<AccessReviews />} />
                <Route path="compliance" element={<Compliance />} />
                <Route path="applications" element={<Applications />} />
                <Route path="evidence" element={<GovernanceEvidence />} />
                <Route path="my-access" element={<MyAccess />} />
            </Route>
        </Routes>
    );
}

/**
 * Ant Design Theme Configuration
 */
function ThemedApp() {
    const { isDark } = useTheme();

    return (
        <ConfigProvider
            theme={{
                algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
                token: {
                    colorPrimary: '#1677ff',
                    borderRadius: 8,
                    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                },
                components: {
                    Layout: {
                        siderBg: isDark ? '#141414' : '#fff',
                        headerBg: isDark ? '#141414' : '#fff',
                        bodyBg: isDark ? '#000' : '#f5f5f5',
                    },
                    Menu: {
                        darkItemBg: '#141414',
                        darkSubMenuItemBg: '#141414',
                    },
                },
            }}
        >
            <AntApp>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </AntApp>
        </ConfigProvider>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <ThemedApp />
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App
