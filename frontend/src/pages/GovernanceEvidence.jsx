import { useState, useEffect } from 'react'
import {
    Card, Table, Tag, Typography, Space, Input, Select, DatePicker,
    Spin, Row, Col, Statistic, Alert
} from 'antd'
import {
    SafetyCertificateOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    FileProtectOutlined,
    LockOutlined,
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Title, Text } = Typography;
const { Search } = Input;
const { RangePicker } = DatePicker;

const API_BASE = 'http://localhost:8000';

/**
 * Governance Evidence Page
 * Read-only evidence for Auditor/Compliance roles
 */
function GovernanceEvidence() {
    const [evidence, setEvidence] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({});
    const { user } = useAuth();

    useEffect(() => {
        fetchEvidence();
    }, [filters]);

    async function fetchEvidence() {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (filters.evidence_type) params.append('evidence_type', filters.evidence_type);
            if (filters.application_id) params.append('application_id', filters.application_id);

            const res = await fetch(`${API_BASE}/grc/evidence?${params}`);
            const data = await res.json();
            setEvidence(data);
        } catch (error) {
            console.error('Failed to load evidence:', error);
        } finally {
            setLoading(false);
        }
    }

    const stats = {
        total: evidence.length,
        granted: evidence.filter(e => e.evidence_type === 'ACCESS_GRANTED').length,
        revoked: evidence.filter(e => e.evidence_type === 'ACCESS_REVOKED').length,
        approvals: evidence.filter(e => e.evidence_type === 'APPROVAL_RECORDED').length,
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
                    <Text type="secondary" style={{ fontSize: 11 }}>{new Date(ts).toLocaleTimeString()}</Text>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'evidence_type',
            key: 'evidence_type',
            render: (type) => {
                const config = {
                    ACCESS_GRANTED: { color: 'green', icon: <CheckCircleOutlined /> },
                    ACCESS_REVOKED: { color: 'red', icon: <CloseCircleOutlined /> },
                    APPROVAL_RECORDED: { color: 'blue', icon: <FileProtectOutlined /> },
                    POLICY_VIOLATION: { color: 'orange', icon: <LockOutlined /> },
                };
                const cfg = config[type] || { color: 'default' };
                return <Tag color={cfg.color} icon={cfg.icon}>{type}</Tag>;
            },
        },
        {
            title: 'Identity',
            dataIndex: 'identity_name',
            key: 'identity_name',
            render: (name) => name || <Text type="secondary">—</Text>,
        },
        {
            title: 'Application',
            dataIndex: 'application_name',
            key: 'application_name',
            render: (name) => name || <Text type="secondary">—</Text>,
        },
        {
            title: 'Entitlement',
            dataIndex: 'entitlement_name',
            key: 'entitlement_name',
            render: (name) => name || <Text type="secondary">—</Text>,
        },
        {
            title: 'Actor',
            dataIndex: 'actor',
            key: 'actor',
        },
        {
            title: 'Action',
            dataIndex: 'action',
            key: 'action',
            render: (action) => <Text code>{action}</Text>,
        },
        {
            title: 'Reference',
            dataIndex: 'immutable_reference',
            key: 'immutable_reference',
            width: 120,
            render: (ref) => (
                <Text copyable={{ text: ref }} style={{ fontSize: 11 }}>
                    {ref?.slice(0, 12)}...
                </Text>
            ),
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ margin: 0 }}>Governance Evidence</Title>
                <Text type="secondary">Immutable evidence records for compliance and audit</Text>
            </div>

            {/* Info Banner */}
            <Alert
                message="Read-Only Evidence"
                description="Evidence records are auto-generated from audit events and cannot be modified. Each record has an immutable SHA-256 reference."
                type="info"
                showIcon
                icon={<SafetyCertificateOutlined />}
                style={{ marginBottom: 16 }}
            />

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic title="Total Evidence" value={stats.total} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Access Granted"
                            value={stats.granted}
                            valueStyle={{ color: '#52c41a' }}
                            prefix={<CheckCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Access Revoked"
                            value={stats.revoked}
                            valueStyle={{ color: '#ff4d4f' }}
                            prefix={<CloseCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Approvals"
                            value={stats.approvals}
                            valueStyle={{ color: '#1677ff' }}
                            prefix={<FileProtectOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Filters */}
            <Card size="small" style={{ marginBottom: 16 }}>
                <Space wrap>
                    <Select
                        placeholder="Evidence Type"
                        allowClear
                        style={{ width: 200 }}
                        onChange={(v) => setFilters({ ...filters, evidence_type: v })}
                    >
                        <Select.Option value="ACCESS_GRANTED">Access Granted</Select.Option>
                        <Select.Option value="ACCESS_REVOKED">Access Revoked</Select.Option>
                        <Select.Option value="APPROVAL_RECORDED">Approval Recorded</Select.Option>
                        <Select.Option value="POLICY_VIOLATION">Policy Violation</Select.Option>
                    </Select>
                </Space>
            </Card>

            {/* Table */}
            <Card>
                <Table
                    dataSource={evidence}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 15 }}
                    size="small"
                />
            </Card>
        </div>
    );
}

export default GovernanceEvidence;
