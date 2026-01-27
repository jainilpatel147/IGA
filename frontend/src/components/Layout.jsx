import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, Space, Typography, Tag } from 'antd'
import {
    DashboardOutlined,
    TeamOutlined,
    KeyOutlined,
    SafetyCertificateOutlined,
    DatabaseOutlined,
    AuditOutlined,
    SunOutlined,
    MoonOutlined,
    LogoutOutlined,
    UserOutlined,
    ApiOutlined,
    LinkOutlined,
    CheckSquareOutlined,
    PieChartOutlined,
    AppstoreOutlined,
    FileProtectOutlined,
    UnlockOutlined,
} from '@ant-design/icons'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'

const { Sider, Header, Content } = AntLayout;
const { Text } = Typography;

// IGA has simple roles: admin and user
// GRC roles (compliance, auditor, reviewer) are managed as application entitlements
const ROLE_MENUS = {
    admin: [
        '/', '/identities', '/access-requests', '/roles', '/resources',
        '/applications', '/access-reviews', '/audit', '/compliance',
        '/evidence', '/api-keys', '/connectors'
    ],
    user: ['/', '/my-access', '/access-requests', '/applications'],
};

/**
 * Layout Component with Role-Based Navigation
 * IGA has simplified admin/user roles
 */
function Layout() {
    const navigate = useNavigate();
    const location = useLocation();
    const { isDark, toggleTheme } = useTheme();
    const { user, logout } = useAuth();

    const userRole = user?.role || 'user';
    const allowedPaths = ROLE_MENUS[userRole] || ROLE_MENUS.user;

    // Filter menu items based on role
    function filterByRole(items) {
        return items.map(item => {
            if (item.type === 'divider') return item;
            if (item.type === 'group') {
                const filteredChildren = item.children.filter(child => allowedPaths.includes(child.key));
                if (filteredChildren.length === 0) return null;
                return { ...item, children: filteredChildren };
            }
            if (!allowedPaths.includes(item.key)) return null;
            return item;
        }).filter(Boolean);
    }

    const allMenuItems = [
        {
            key: '/',
            icon: <DashboardOutlined />,
            label: 'Dashboard',
        },
        {
            type: 'divider',
        },
        // User-specific: My Access
        ...(userRole === 'user' ? [{
            key: '/my-access',
            icon: <UnlockOutlined />,
            label: 'My Access',
        }] : []),
        // Identity Management (Admin only)
        {
            key: 'identity-group',
            label: 'Identity Management',
            type: 'group',
            children: [
                {
                    key: '/identities',
                    icon: <TeamOutlined />,
                    label: 'Identities',
                },
                {
                    key: '/access-requests',
                    icon: <KeyOutlined />,
                    label: 'Access Requests',
                },
                {
                    key: '/roles',
                    icon: <SafetyCertificateOutlined />,
                    label: 'Roles',
                },
                {
                    key: '/resources',
                    icon: <DatabaseOutlined />,
                    label: 'Resources',
                },
            ],
        },
        // Applications
        {
            key: 'apps-group',
            label: 'Applications',
            type: 'group',
            children: [
                {
                    key: '/applications',
                    icon: <AppstoreOutlined />,
                    label: 'Application Registry',
                },
            ],
        },
        // Governance (Admin only)
        {
            key: 'governance-group',
            label: 'Governance',
            type: 'group',
            children: [
                {
                    key: '/access-reviews',
                    icon: <CheckSquareOutlined />,
                    label: 'Access Reviews',
                },
                {
                    key: '/audit',
                    icon: <AuditOutlined />,
                    label: 'Audit Log',
                },
                {
                    key: '/evidence',
                    icon: <FileProtectOutlined />,
                    label: 'Evidence',
                },
                {
                    key: '/compliance',
                    icon: <PieChartOutlined />,
                    label: 'Compliance',
                },
            ],
        },
        // Integration (Admin only)
        {
            key: 'integration-group',
            label: 'Integration',
            type: 'group',
            children: [
                {
                    key: '/api-keys',
                    icon: <ApiOutlined />,
                    label: 'API Keys',
                },
                {
                    key: '/connectors',
                    icon: <LinkOutlined />,
                    label: 'Connectors',
                },
            ],
        },
    ];

    const menuItems = filterByRole(allMenuItems);

    const roleColors = {
        admin: 'red',
        user: 'green',
    };

    const userMenuItems = [
        {
            key: 'role',
            label: <Tag color={roleColors[userRole]}>{userRole.toUpperCase()}</Tag>,
            disabled: true,
        },
        { type: 'divider' },
        {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: 'Sign Out',
            danger: true,
        },
    ];

    const handleUserMenuClick = ({ key }) => {
        if (key === 'logout') {
            logout();
            navigate('/login');
        }
    };

    return (
        <AntLayout style={{ minHeight: '100vh' }}>
            {/* Sidebar */}
            <Sider
                width={240}
                style={{
                    position: 'fixed',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    overflow: 'auto',
                }}
            >
                {/* Logo */}
                <div style={{
                    height: 64,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderBottom: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
                }}>
                    <Space>
                        <SafetyCertificateOutlined style={{ fontSize: 24, color: '#1677ff' }} />
                        <Text strong style={{ fontSize: 18 }}>IGA Platform</Text>
                    </Space>
                </div>

                {/* Menu */}
                <Menu
                    mode="inline"
                    selectedKeys={[location.pathname]}
                    items={menuItems}
                    onClick={({ key }) => navigate(key)}
                    style={{ borderRight: 0, marginTop: 8 }}
                />
            </Sider>

            {/* Main Content */}
            <AntLayout style={{ marginLeft: 240 }}>
                {/* Header */}
                <Header style={{
                    padding: '0 24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: 16,
                    position: 'sticky',
                    top: 0,
                    zIndex: 100,
                    borderBottom: `1px solid ${isDark ? '#303030' : '#f0f0f0'}`,
                }}>
                    {/* Theme Toggle */}
                    <Button
                        type="text"
                        icon={isDark ? <SunOutlined /> : <MoonOutlined />}
                        onClick={toggleTheme}
                        style={{ fontSize: 18 }}
                    />

                    {/* User Menu */}
                    <Dropdown
                        menu={{
                            items: userMenuItems,
                            onClick: handleUserMenuClick,
                        }}
                        placement="bottomRight"
                    >
                        <Space style={{ cursor: 'pointer' }}>
                            <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1677ff' }} />
                            <Text strong>{user?.username || 'Admin'}</Text>
                        </Space>
                    </Dropdown>
                </Header>

                {/* Content */}
                <Content style={{ padding: 24, minHeight: 'calc(100vh - 64px)' }}>
                    <Outlet />
                </Content>
            </AntLayout>
        </AntLayout>
    );
}

export default Layout;
