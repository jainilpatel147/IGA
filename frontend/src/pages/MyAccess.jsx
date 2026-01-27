import { useState, useEffect } from 'react'
import {
    Card, Table, Tag, Typography, Space, Row, Col, Statistic, Button,
    Empty, Spin, Alert
} from 'antd'
import {
    AppstoreOutlined,
    SafetyCertificateOutlined,
    PlusOutlined,
} from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getIdentities } from '../api/client'

const { Title, Text } = Typography;

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * My Access Page
 * View own access (User role)
 */
function MyAccess() {
    const [access, setAccess] = useState([]);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();

    useEffect(() => {
        fetchMyAccess();
    }, []);

    async function fetchMyAccess() {
        try {
            setLoading(true);
            // In a real app, this would filter by the current user's identity
            // For demo, we show all applications and their access
            const appsRes = await fetch(`${API_BASE}/applications`);
            const apps = await appsRes.json();

            // Collect all access we have
            const allAccess = [];
            for (const app of apps) {
                try {
                    const accessRes = await fetch(`${API_BASE}/applications/${app.id}/access`);
                    const appAccess = await accessRes.json();
                    for (const a of appAccess) {
                        allAccess.push({
                            ...a,
                            application_name: app.name,
                        });
                    }
                } catch (e) {
                    // Skip apps we can't access
                }
            }

            setAccess(allAccess);
        } catch (error) {
            console.error('Failed to load access:', error);
        } finally {
            setLoading(false);
        }
    }

    const columns = [
        {
            title: 'Application',
            dataIndex: 'application_name',
            key: 'application_name',
            render: (name) => (
                <Space>
                    <AppstoreOutlined style={{ color: '#1677ff' }} />
                    <Text strong>{name}</Text>
                </Space>
            ),
        },
        {
            title: 'Entitlement',
            dataIndex: 'entitlement_name',
            key: 'entitlement_name',
            render: (name) => <Tag color="blue">{name}</Tag>,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => (
                <Tag color={status === 'active' ? 'green' : 'default'}>
                    {status.toUpperCase()}
                </Tag>
            ),
        },
        {
            title: 'Granted',
            dataIndex: 'granted_at',
            key: 'granted_at',
            render: (date) => new Date(date).toLocaleDateString(),
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            render: (date) => date ? new Date(date).toLocaleDateString() : <Text type="secondary">Never</Text>,
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>My Access</Title>
                    <Text type="secondary">View your current application access</Text>
                </div>
                <Link to="/access-requests">
                    <Button type="primary" icon={<PlusOutlined />}>Request Access</Button>
                </Link>
            </div>

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Active Access"
                            value={access.filter(a => a.status === 'active').length}
                            prefix={<SafetyCertificateOutlined style={{ color: '#52c41a' }} />}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Applications"
                            value={new Set(access.map(a => a.application_name)).size}
                            prefix={<AppstoreOutlined style={{ color: '#1677ff' }} />}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Expiring Soon"
                            value={access.filter(a => {
                                if (!a.expires_at) return false;
                                const exp = new Date(a.expires_at);
                                const now = new Date();
                                const diff = (exp - now) / (1000 * 60 * 60 * 24);
                                return diff > 0 && diff < 30;
                            }).length}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Access Table */}
            <Card>
                {access.length > 0 ? (
                    <Table dataSource={access} columns={columns} rowKey="id" />
                ) : (
                    <Empty
                        description="No access assigned"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                    >
                        <Link to="/access-requests">
                            <Button type="primary">Request Access</Button>
                        </Link>
                    </Empty>
                )}
            </Card>
        </div>
    );
}

export default MyAccess;
