import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Row, Col, Card, Statistic, Table, Tag, Typography, Space, Button, Spin } from 'antd'
import {
    TeamOutlined,
    ClockCircleOutlined,
    CheckCircleOutlined,
    AuditOutlined,
    ArrowUpOutlined,
    PlusOutlined,
    EyeOutlined,
} from '@ant-design/icons'
import { getIdentities, getAccessRequests, getAuditEvents } from '../api/client'

const { Title, Text } = Typography;

/**
 * Dashboard Page with Ant Design
 */
function Dashboard() {
    const [stats, setStats] = useState({
        identities: 0,
        pendingRequests: 0,
        approvedRequests: 0,
        auditEvents: 0,
    });
    const [recentEvents, setRecentEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    async function fetchDashboardData() {
        try {
            setLoading(true);
            const [identities, requests, events] = await Promise.all([
                getIdentities(),
                getAccessRequests(),
                getAuditEvents()
            ]);

            setStats({
                identities: identities.length,
                pendingRequests: requests.filter(r => r.status === 'pending').length,
                approvedRequests: requests.filter(r => r.status === 'approved').length,
                auditEvents: events.length,
            });

            setRecentEvents(events.slice(0, 5));
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    }

    const columns = [
        {
            title: 'Time',
            dataIndex: 'timestamp',
            key: 'timestamp',
            render: (ts) => new Date(ts).toLocaleString(),
        },
        {
            title: 'Type',
            dataIndex: 'event_type',
            key: 'event_type',
            render: (type) => <Tag color="blue">{type}</Tag>,
        },
        {
            title: 'Action',
            dataIndex: 'action',
            key: 'action',
            render: (action) => <Text strong>{action}</Text>,
        },
        {
            title: 'Actor',
            dataIndex: 'actor',
            key: 'actor',
        },
        {
            title: 'Decision',
            dataIndex: 'decision',
            key: 'decision',
            render: (decision) => {
                const colors = { allow: 'green', deny: 'red', pending: 'orange' };
                return <Tag color={colors[decision] || 'default'}>{decision}</Tag>;
            },
        },
    ];

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
                <Spin size="large" />
            </div>
        );
    }

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ margin: 0 }}>Dashboard</Title>
                <Text type="secondary">Identity Governance & Administration Overview</Text>
            </div>

            {/* Stats Cards */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} md={6}>
                    <Card hoverable>
                        <Statistic
                            title="Total Identities"
                            value={stats.identities}
                            prefix={<TeamOutlined style={{ color: '#1677ff' }} />}
                            suffix={<Text type="success" style={{ fontSize: 14 }}><ArrowUpOutlined /> Active</Text>}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card hoverable>
                        <Statistic
                            title="Pending Requests"
                            value={stats.pendingRequests}
                            prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
                            valueStyle={stats.pendingRequests > 0 ? { color: '#fa8c16' } : {}}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card hoverable>
                        <Statistic
                            title="Approved Access"
                            value={stats.approvedRequests}
                            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card hoverable>
                        <Statistic
                            title="Audit Events"
                            value={stats.auditEvents}
                            prefix={<AuditOutlined style={{ color: '#13c2c2' }} />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Quick Actions */}
            <Card title="Quick Actions" style={{ marginBottom: 24 }}>
                <Space wrap>
                    <Link to="/identities">
                        <Button type="primary" icon={<PlusOutlined />}>Create Identity</Button>
                    </Link>
                    <Link to="/access-requests">
                        <Button icon={<EyeOutlined />}>Review Requests</Button>
                    </Link>
                    <Link to="/audit">
                        <Button icon={<AuditOutlined />}>View Audit Log</Button>
                    </Link>
                </Space>
            </Card>

            {/* Recent Activity */}
            <Card
                title="Recent Audit Activity"
                extra={<Link to="/audit"><Button type="link">View All</Button></Link>}
            >
                <Table
                    dataSource={recentEvents}
                    columns={columns}
                    rowKey="event_id"
                    pagination={false}
                    size="middle"
                />
            </Card>
        </div>
    );
}

export default Dashboard;
