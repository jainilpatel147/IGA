import { useState, useEffect } from 'react'
import {
    Card, Table, Tag, Typography, Space, Row, Col, Statistic,
    Input, Segmented, Button, Spin
} from 'antd'
import {
    AuditOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    ReloadOutlined,
    LockOutlined,
} from '@ant-design/icons'
import { getAuditEvents } from '../api/client'

const { Title, Text } = Typography;
const { Search } = Input;

/**
 * Audit Log Page with Ant Design
 */
function AuditLog() {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchEvents();
    }, []);

    async function fetchEvents() {
        try {
            setLoading(true);
            const data = await getAuditEvents();
            setEvents(data);
        } catch (error) {
            console.error('Failed to load audit events:', error);
        } finally {
            setLoading(false);
        }
    }

    const eventTypes = ['all', ...new Set(events.map(e => e.event_type))];

    const filteredEvents = events.filter(e => {
        const matchesFilter = filter === 'all' || e.event_type === filter;
        const matchesSearch = !searchTerm ||
            e.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.target.toLowerCase().includes(searchTerm.toLowerCase()) ||
            e.action.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    const stats = {
        total: events.length,
        allow: events.filter(e => e.decision === 'allow').length,
        deny: events.filter(e => e.decision === 'deny').length,
        pending: events.filter(e => e.decision === 'pending').length,
    };

    const columns = [
        {
            title: 'Timestamp',
            dataIndex: 'timestamp',
            key: 'timestamp',
            width: 180,
            render: (ts) => (
                <Space direction="vertical" size={0}>
                    <Text>{new Date(ts).toLocaleDateString()}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{new Date(ts).toLocaleTimeString()}</Text>
                </Space>
            ),
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
            title: 'Target',
            dataIndex: 'target',
            key: 'target',
            ellipsis: true,
        },
        {
            title: 'Decision',
            dataIndex: 'decision',
            key: 'decision',
            render: (decision) => {
                const config = {
                    allow: { color: 'green', icon: <CheckCircleOutlined /> },
                    deny: { color: 'red', icon: <CloseCircleOutlined /> },
                    pending: { color: 'orange', icon: <ClockCircleOutlined /> },
                };
                const cfg = config[decision] || { color: 'default' };
                return <Tag color={cfg.color} icon={cfg.icon}>{decision}</Tag>;
            },
        },
        {
            title: 'Reason',
            dataIndex: 'reason',
            key: 'reason',
            ellipsis: true,
            render: (reason) => reason || <Text type="secondary">—</Text>,
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
            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ margin: 0 }}>Audit Log</Title>
                <Text type="secondary">Immutable record of all system actions</Text>
            </div>

            {/* Stats Cards */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Total Events" value={stats.total} prefix={<AuditOutlined />} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Allowed" value={stats.allow} prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />} valueStyle={{ color: '#52c41a' }} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Pending" value={stats.pending} prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />} valueStyle={{ color: '#fa8c16' }} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Denied" value={stats.deny} prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />} valueStyle={{ color: '#ff4d4f' }} />
                    </Card>
                </Col>
            </Row>

            {/* Info Banner */}
            <Card size="small" style={{ marginBottom: 16, background: '#f6ffed', borderColor: '#b7eb8f' }}>
                <Space>
                    <LockOutlined style={{ color: '#52c41a' }} />
                    <Text><strong>Immutable Audit Trail</strong> — Events are append-only and cannot be modified or deleted.</Text>
                </Space>
            </Card>

            {/* Filters */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 16 }}>
                <Segmented
                    options={eventTypes.map(t => ({ label: t === 'all' ? 'All Events' : t, value: t }))}
                    value={filter}
                    onChange={setFilter}
                />
                <Space>
                    <Search
                        placeholder="Search events..."
                        allowClear
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{ width: 200 }}
                    />
                    <Button icon={<ReloadOutlined />} onClick={fetchEvents}>Refresh</Button>
                </Space>
            </div>

            {/* Table */}
            <Card>
                <Table
                    dataSource={filteredEvents}
                    columns={columns}
                    rowKey="event_id"
                    pagination={{ pageSize: 10, showSizeChanger: true }}
                />
            </Card>
        </div>
    );
}

export default AuditLog;
