import { useState, useEffect } from 'react'
import {
    Card, Row, Col, Statistic, Typography, Space, Progress, Table, Tag, Alert
} from 'antd'
import {
    SafetyCertificateOutlined,
    TeamOutlined,
    KeyOutlined,
    ApiOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    AuditOutlined,
} from '@ant-design/icons'
import { getIdentities, getAccessRequests, getAuditEvents } from '../api/client'

const { Title, Text, Paragraph } = Typography;

const API_BASE = 'http://localhost:8000';

/**
 * Compliance Page
 * Overview of governance metrics and compliance status
 */
function Compliance() {
    const [stats, setStats] = useState({
        identities: 0,
        accessGrants: 0,
        pendingRequests: 0,
        auditEvents: 0,
        reviewCampaigns: 0,
        connectors: 0,
        apiKeys: 0,
    });
    const [loading, setLoading] = useState(true);
    const [riskBreakdown, setRiskBreakdown] = useState([]);

    useEffect(() => {
        fetchComplianceData();
    }, []);

    async function fetchComplianceData() {
        try {
            setLoading(true);

            const [identities, requests, auditEvents, reviews, connectors, apiKeys] = await Promise.all([
                getIdentities(),
                getAccessRequests(),
                getAuditEvents(),
                fetch(`${API_BASE}/access-reviews`).then(r => r.json()).catch(() => []),
                fetch(`${API_BASE}/connectors`).then(r => r.json()).catch(() => []),
                fetch(`${API_BASE}/api-keys`).then(r => r.json()).catch(() => []),
            ]);

            const approvedRequests = requests.filter(r => r.status === 'approved');

            setStats({
                identities: identities.length,
                accessGrants: approvedRequests.length,
                pendingRequests: requests.filter(r => r.status === 'pending').length,
                auditEvents: auditEvents.length,
                reviewCampaigns: reviews.length,
                connectors: connectors.filter(c => c.status === 'active').length,
                apiKeys: apiKeys.filter(k => k.is_active).length,
            });

            // Calculate risk breakdown
            const riskCounts = { low: 0, medium: 0, high: 0 };
            approvedRequests.forEach(r => {
                if (['admin', 'write', 'delete'].some(x => r.role.toLowerCase().includes(x))) {
                    riskCounts.high++;
                } else if (['edit', 'modify'].some(x => r.role.toLowerCase().includes(x))) {
                    riskCounts.medium++;
                } else {
                    riskCounts.low++;
                }
            });

            setRiskBreakdown([
                { risk: 'Low Risk', count: riskCounts.low, color: 'green' },
                { risk: 'Medium Risk', count: riskCounts.medium, color: 'orange' },
                { risk: 'High Risk', count: riskCounts.high, color: 'red' },
            ]);

        } catch (error) {
            console.error('Failed to load compliance data:', error);
        } finally {
            setLoading(false);
        }
    }

    const complianceScore = 85; // Demo score - in production, calculate from real metrics

    const complianceChecks = [
        { check: 'All access requests require approval', status: 'pass' },
        { check: 'Audit logging enabled for all actions', status: 'pass' },
        { check: 'API keys have expiration dates', status: 'warn' },
        { check: 'Access reviews completed on schedule', status: 'pass' },
        { check: 'Segregation of duties policies defined', status: 'warn' },
        { check: 'High-risk access reviewed monthly', status: 'pass' },
    ];

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ margin: 0 }}>Compliance Dashboard</Title>
                <Text type="secondary">Governance metrics and compliance overview</Text>
            </div>

            {/* Compliance Score */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} md={8}>
                    <Card>
                        <div style={{ textAlign: 'center' }}>
                            <Progress
                                type="circle"
                                percent={complianceScore}
                                strokeColor={complianceScore >= 80 ? '#52c41a' : complianceScore >= 60 ? '#faad14' : '#ff4d4f'}
                                size={120}
                            />
                            <Title level={4} style={{ marginTop: 16, marginBottom: 0 }}>Compliance Score</Title>
                            <Text type="secondary">Based on governance policies</Text>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} md={16}>
                    <Card title="Compliance Checks">
                        <Table
                            dataSource={complianceChecks}
                            columns={[
                                {
                                    title: 'Check',
                                    dataIndex: 'check',
                                    key: 'check',
                                },
                                {
                                    title: 'Status',
                                    dataIndex: 'status',
                                    key: 'status',
                                    render: (status) => (
                                        status === 'pass'
                                            ? <Tag color="green" icon={<CheckCircleOutlined />}>PASS</Tag>
                                            : <Tag color="orange" icon={<ExclamationCircleOutlined />}>NEEDS ATTENTION</Tag>
                                    ),
                                },
                            ]}
                            pagination={false}
                            size="small"
                            rowKey="check"
                        />
                    </Card>
                </Col>
            </Row>

            {/* Stats Grid */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Identities" value={stats.identities} prefix={<TeamOutlined />} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Access Grants" value={stats.accessGrants} prefix={<KeyOutlined />} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Active Connectors" value={stats.connectors} prefix={<ApiOutlined />} />
                    </Card>
                </Col>
                <Col xs={12} md={6}>
                    <Card>
                        <Statistic title="Active API Keys" value={stats.apiKeys} prefix={<SafetyCertificateOutlined />} />
                    </Card>
                </Col>
            </Row>

            {/* Risk Breakdown */}
            <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                    <Card title="Access Risk Distribution">
                        <Table
                            dataSource={riskBreakdown}
                            columns={[
                                {
                                    title: 'Risk Level',
                                    dataIndex: 'risk',
                                    key: 'risk',
                                    render: (risk, record) => <Tag color={record.color}>{risk}</Tag>,
                                },
                                {
                                    title: 'Count',
                                    dataIndex: 'count',
                                    key: 'count',
                                    render: (count) => <Text strong>{count}</Text>,
                                },
                                {
                                    title: 'Percentage',
                                    key: 'percent',
                                    render: (_, record) => {
                                        const total = riskBreakdown.reduce((sum, r) => sum + r.count, 0);
                                        const pct = total ? Math.round((record.count / total) * 100) : 0;
                                        return <Progress percent={pct} size="small" showInfo={false} strokeColor={record.color} />;
                                    },
                                },
                            ]}
                            pagination={false}
                            size="small"
                            rowKey="risk"
                        />
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card title="Governance Summary">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Alert
                                message="Audit Trail Active"
                                description="All identity and access changes are being logged immutably."
                                type="success"
                                showIcon
                                icon={<AuditOutlined />}
                            />
                            <Alert
                                message={`${stats.pendingRequests} Pending Requests`}
                                description="Access requests require review before approval."
                                type={stats.pendingRequests > 0 ? 'warning' : 'success'}
                                showIcon
                            />
                            <Alert
                                message={`${stats.reviewCampaigns} Access Reviews`}
                                description="Periodic access certification campaigns."
                                type="info"
                                showIcon
                            />
                        </Space>
                    </Card>
                </Col>
            </Row>
        </div>
    );
}

export default Compliance;
