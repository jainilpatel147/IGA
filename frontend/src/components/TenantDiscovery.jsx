/**
 * Tenant Discovery Component
 * Shows discovery jobs and discovered tenants pending approval
 * 
 * KEY ARCHITECTURAL POINTS:
 * - Discovered tenants start as PENDING_ONBOARDING
 * - Admin must approve before governance begins
 * - SSO connectors cannot discover tenants
 */

import { useState, useEffect } from 'react';
import {
    Card, Table, Button, Space, Tag, Empty, Badge, Modal,
    Tabs, message, Typography, Statistic, Row, Col, Input,
    Tooltip, Progress, Timeline
} from 'antd';
import {
    SearchOutlined, CheckCircleOutlined, CloseCircleOutlined,
    ClockCircleOutlined, TeamOutlined, SyncOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import api from '../api/request';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

function TenantDiscovery({ applicationId, isCloud }) {
    const [discoveredTenants, setDiscoveredTenants] = useState([]);
    const [discoveryJobs, setDiscoveryJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [approveModal, setApproveModal] = useState({ visible: false, tenant: null });
    const [rejectModal, setRejectModal] = useState({ visible: false, tenant: null });
    const [justification, setJustification] = useState('');
    const [reason, setReason] = useState('');
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        fetchData();
    }, [applicationId]);

    async function fetchData() {
        try {
            setLoading(true);

            // Fetch discovered tenants
            const tenantData = await api.get(`/applications/${applicationId}/discovered-tenants`);
            setDiscoveredTenants(tenantData.tenants || []);

            // Fetch discovery jobs
            const jobData = await api.get(`/applications/${applicationId}/discovery-jobs`);
            setDiscoveryJobs(jobData.jobs || []);
        } catch (error) {
            console.error('Failed to load discovery data:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleApprove() {
        try {
            setProcessing(true);
            await api.post(`/applications/tenants/${approveModal.tenant.id}/approve`, {
                justification
            });
            message.success(`Tenant "${approveModal.tenant.name}" approved for governance`);
            setApproveModal({ visible: false, tenant: null });
            setJustification('');
            fetchData();
        } catch (error) {
            message.error(error.message || 'Failed to approve tenant');
        } finally {
            setProcessing(false);
        }
    }

    async function handleReject() {
        try {
            setProcessing(true);
            await api.post(`/applications/tenants/${rejectModal.tenant.id}/reject`, {
                reason
            });
            message.success(`Tenant "${rejectModal.tenant.name}" rejected`);
            setRejectModal({ visible: false, tenant: null });
            setReason('');
            fetchData();
        } catch (error) {
            message.error(error.message || 'Failed to reject tenant');
        } finally {
            setProcessing(false);
        }
    }

    const pendingTenants = discoveredTenants.filter(t => t.onboarding_status === 'pending_onboarding');
    const approvedTenants = discoveredTenants.filter(t => t.onboarding_status === 'approved');
    const rejectedTenants = discoveredTenants.filter(t => t.onboarding_status === 'rejected');

    const tenantColumns = [
        {
            title: 'Tenant',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <TeamOutlined style={{ fontSize: 18, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" code style={{ fontSize: 11 }}>
                            {record.external_id}
                        </Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'onboarding_status',
            key: 'onboarding_status',
            render: (status) => {
                const config = {
                    pending_onboarding: { color: 'warning', icon: <ClockCircleOutlined />, text: 'Pending' },
                    approved: { color: 'success', icon: <CheckCircleOutlined />, text: 'Approved' },
                    rejected: { color: 'error', icon: <CloseCircleOutlined />, text: 'Rejected' },
                };
                const cfg = config[status] || { color: 'default', text: status };
                return <Tag color={cfg.color} icon={cfg.icon}>{cfg.text}</Tag>;
            },
        },
        {
            title: 'External Metadata',
            dataIndex: 'external_metadata',
            key: 'external_metadata',
            render: (meta) => {
                if (!meta || Object.keys(meta).length === 0) return '-';
                return (
                    <Tooltip title={JSON.stringify(meta, null, 2)}>
                        <Space>
                            {meta.plan && <Tag color="blue">{meta.plan}</Tag>}
                            {meta.seats && <Text type="secondary">{meta.seats} seats</Text>}
                        </Space>
                    </Tooltip>
                );
            },
        },
        {
            title: 'Discovered',
            dataIndex: 'discovered_at',
            key: 'discovered_at',
            render: (date) => date ? new Date(date).toLocaleString() : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                record.onboarding_status === 'pending_onboarding' && (
                    <Space>
                        <Button
                            type="primary"
                            size="small"
                            icon={<CheckCircleOutlined />}
                            onClick={() => setApproveModal({ visible: true, tenant: record })}
                        >
                            Approve
                        </Button>
                        <Button
                            danger
                            size="small"
                            icon={<CloseCircleOutlined />}
                            onClick={() => setRejectModal({ visible: true, tenant: record })}
                        >
                            Reject
                        </Button>
                    </Space>
                )
            ),
        },
    ];

    const jobColumns = [
        {
            title: 'Job ID',
            dataIndex: 'id',
            key: 'id',
            render: (id) => <Text code>{id?.substring(0, 8)}...</Text>,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const config = {
                    pending: { color: 'default', text: 'Pending' },
                    running: { color: 'processing', text: 'Running' },
                    completed: { color: 'success', text: 'Completed' },
                    failed: { color: 'error', text: 'Failed' },
                };
                const cfg = config[status] || { color: 'default', text: status };
                return <Tag color={cfg.color}>{cfg.text}</Tag>;
            },
        },
        {
            title: 'Triggered By',
            dataIndex: 'triggered_by',
            key: 'triggered_by',
        },
        {
            title: 'Results',
            key: 'results',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Discovered">
                        <Tag>{record.discovered_count} found</Tag>
                    </Tooltip>
                    <Tooltip title="Created">
                        <Tag color="green">+{record.created_count}</Tag>
                    </Tooltip>
                    <Tooltip title="Updated">
                        <Tag color="blue">~{record.updated_count}</Tag>
                    </Tooltip>
                    <Tooltip title="Deactivated">
                        <Tag color="orange">-{record.deactivated_count}</Tag>
                    </Tooltip>
                </Space>
            ),
        },
        {
            title: 'Completed',
            dataIndex: 'completed_at',
            key: 'completed_at',
            render: (date) => date ? new Date(date).toLocaleString() : '-',
        },
    ];

    if (!isCloud) {
        return (
            <Card>
                <Empty
                    description={
                        <span>
                            Tenant discovery is only available for<br />
                            <strong>Cloud (Multi-Tenant)</strong> applications
                        </span>
                    }
                />
            </Card>
        );
    }

    return (
        <div>
            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Pending Approval"
                            value={pendingTenants.length}
                            valueStyle={{ color: '#faad14' }}
                            prefix={<ClockCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Approved"
                            value={approvedTenants.length}
                            valueStyle={{ color: '#52c41a' }}
                            prefix={<CheckCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Rejected"
                            value={rejectedTenants.length}
                            valueStyle={{ color: '#ff4d4f' }}
                            prefix={<CloseCircleOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Discovery Jobs"
                            value={discoveryJobs.length}
                            prefix={<SyncOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Tabs for Tenants and Jobs */}
            <Card>
                <Tabs
                    defaultActiveKey="pending"
                    items={[
                        {
                            key: 'pending',
                            label: (
                                <Space>
                                    <ClockCircleOutlined />
                                    Pending Approval
                                    {pendingTenants.length > 0 && (
                                        <Badge count={pendingTenants.length} size="small" />
                                    )}
                                </Space>
                            ),
                            children: (
                                <Table
                                    dataSource={pendingTenants}
                                    columns={tenantColumns}
                                    rowKey="id"
                                    loading={loading}
                                    pagination={false}
                                    locale={{ emptyText: <Empty description="No tenants pending approval" /> }}
                                />
                            ),
                        },
                        {
                            key: 'all',
                            label: (
                                <Space>
                                    <TeamOutlined />
                                    All Discovered ({discoveredTenants.length})
                                </Space>
                            ),
                            children: (
                                <Table
                                    dataSource={discoveredTenants}
                                    columns={tenantColumns}
                                    rowKey="id"
                                    loading={loading}
                                    pagination={false}
                                />
                            ),
                        },
                        {
                            key: 'jobs',
                            label: (
                                <Space>
                                    <SyncOutlined />
                                    Discovery Jobs ({discoveryJobs.length})
                                </Space>
                            ),
                            children: (
                                <Table
                                    dataSource={discoveryJobs}
                                    columns={jobColumns}
                                    rowKey="id"
                                    loading={loading}
                                    pagination={false}
                                />
                            ),
                        },
                    ]}
                />
            </Card>

            {/* Approve Modal */}
            <Modal
                title={
                    <Space>
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        Approve Tenant for Governance
                    </Space>
                }
                open={approveModal.visible}
                onCancel={() => {
                    setApproveModal({ visible: false, tenant: null });
                    setJustification('');
                }}
                onOk={handleApprove}
                confirmLoading={processing}
                okText="Approve"
                okButtonProps={{ type: 'primary' }}
            >
                {approveModal.tenant && (
                    <div>
                        <Paragraph>
                            You are about to approve <strong>{approveModal.tenant.name}</strong> for identity governance.
                        </Paragraph>
                        <Paragraph type="secondary">
                            After approval:
                        </Paragraph>
                        <ul>
                            <li>Tenant will be marked as ACTIVE</li>
                            <li>You can configure tenant-level connectors</li>
                            <li>Identity sync and governance will begin</li>
                        </ul>
                        <TextArea
                            placeholder="Optional: Enter justification for approval"
                            value={justification}
                            onChange={(e) => setJustification(e.target.value)}
                            rows={3}
                        />
                    </div>
                )}
            </Modal>

            {/* Reject Modal */}
            <Modal
                title={
                    <Space>
                        <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                        Reject Tenant
                    </Space>
                }
                open={rejectModal.visible}
                onCancel={() => {
                    setRejectModal({ visible: false, tenant: null });
                    setReason('');
                }}
                onOk={handleReject}
                confirmLoading={processing}
                okText="Reject"
                okButtonProps={{ danger: true }}
            >
                {rejectModal.tenant && (
                    <div>
                        <Paragraph>
                            You are about to reject <strong>{rejectModal.tenant.name}</strong>.
                        </Paragraph>
                        <Paragraph type="warning">
                            Rejected tenants will not be governed by IGA.
                        </Paragraph>
                        <TextArea
                            placeholder="Optional: Enter reason for rejection"
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={3}
                        />
                    </div>
                )}
            </Modal>
        </div>
    );
}

export default TenantDiscovery;
