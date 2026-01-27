import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, Badge, Spin, message, Tabs, Row, Col, Statistic, Tooltip
} from 'antd'
import {
    PlusOutlined,
    AppstoreOutlined,
    SettingOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    TeamOutlined,
    SafetyCertificateOutlined,
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Applications Page
 * Application registry and entitlement management (Admin)
 */
function Applications() {
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [entitlementModal, setEntitlementModal] = useState(null);
    const [accessModal, setAccessModal] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [form] = Form.useForm();
    const [entitlementForm] = Form.useForm();
    const { user } = useAuth();

    useEffect(() => {
        fetchApplications();
    }, []);

    async function fetchApplications() {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/applications`);
            const data = await res.json();
            setApplications(data);
        } catch (error) {
            console.error('Failed to load applications:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateApp(values) {
        try {
            setSubmitting(true);
            const res = await fetch(`${API_BASE}/applications`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(values)
            });
            if (!res.ok) throw new Error('Failed to create');
            message.success('Application registered');
            setModalOpen(false);
            form.resetFields();
            fetchApplications();
        } catch (error) {
            message.error('Failed to create application');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleCreateEntitlement(values) {
        try {
            setSubmitting(true);
            const res = await fetch(`${API_BASE}/applications/${entitlementModal.id}/entitlements`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(values)
            });
            if (!res.ok) throw new Error('Failed to create');
            message.success('Entitlement created');
            entitlementForm.resetFields();
            // Refresh entitlements
            const entRes = await fetch(`${API_BASE}/applications/${entitlementModal.id}/entitlements`);
            setEntitlementModal({ ...entitlementModal, entitlements: await entRes.json() });
        } catch (error) {
            message.error('Failed to create entitlement');
        } finally {
            setSubmitting(false);
        }
    }

    async function openEntitlementModal(app) {
        try {
            const res = await fetch(`${API_BASE}/applications/${app.id}/entitlements`);
            const entitlements = await res.json();
            setEntitlementModal({ ...app, entitlements });
        } catch (error) {
            message.error('Failed to load entitlements');
        }
    }

    async function openAccessModal(app) {
        try {
            const res = await fetch(`${API_BASE}/applications/${app.id}/access`);
            const access = await res.json();
            setAccessModal({ ...app, access });
        } catch (error) {
            message.error('Failed to load access');
        }
    }

    async function updateStatus(appId, status) {
        try {
            await fetch(`${API_BASE}/applications/${appId}/status?status=${status}`, {
                method: 'PATCH'
            });
            message.success('Status updated');
            fetchApplications();
        } catch (error) {
            message.error('Failed to update status');
        }
    }

    const columns = [
        {
            title: 'Application',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <AppstoreOutlined style={{ fontSize: 20, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
        },
        {
            title: 'Integration',
            dataIndex: 'integration_type',
            key: 'integration_type',
            render: (type) => {
                const colors = { api: 'green', token: 'blue', readonly: 'default' };
                return <Tag color={colors[type]}>{type.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const config = {
                    active: { status: 'success', text: 'Active' },
                    inactive: { status: 'default', text: 'Inactive' },
                    pending: { status: 'warning', text: 'Pending' },
                };
                return <Badge {...config[status]} />;
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Manage entitlements">
                        <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => openEntitlementModal(record)}>
                            Entitlements
                        </Button>
                    </Tooltip>
                    <Tooltip title="View access">
                        <Button size="small" icon={<TeamOutlined />} onClick={() => openAccessModal(record)}>
                            Access
                        </Button>
                    </Tooltip>
                    {user?.role === 'admin' && record.status === 'pending' && (
                        <Button size="small" type="primary" onClick={() => updateStatus(record.id, 'active')}>
                            Activate
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    const entitlementColumns = [
        { title: 'Name', dataIndex: 'name', key: 'name' },
        { title: 'Description', dataIndex: 'description', key: 'description' },
        {
            title: 'Risk',
            dataIndex: 'risk_level',
            key: 'risk_level',
            render: (level) => {
                const colors = { low: 'green', medium: 'orange', high: 'red' };
                return <Tag color={colors[level]}>{level.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Privileged',
            dataIndex: 'is_privileged',
            key: 'is_privileged',
            render: (priv) => priv ? <Tag color="red">YES</Tag> : <Tag>NO</Tag>,
        },
    ];

    const accessColumns = [
        { title: 'Identity', dataIndex: 'identity_name', key: 'identity_name' },
        { title: 'Entitlement', dataIndex: 'entitlement_name', key: 'entitlement_name' },
        { title: 'Status', dataIndex: 'status', key: 'status', render: (s) => <Tag color="green">{s}</Tag> },
        {
            title: 'Granted',
            dataIndex: 'granted_at',
            key: 'granted_at',
            render: (d) => new Date(d).toLocaleDateString(),
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>Applications</Title>
                    <Text type="secondary">Govern access to registered applications</Text>
                </div>
                {user?.role === 'admin' && (
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                        Register Application
                    </Button>
                )}
            </div>

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Total Applications" value={applications.length} prefix={<AppstoreOutlined />} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Active"
                            value={applications.filter(a => a.status === 'active').length}
                            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Pending"
                            value={applications.filter(a => a.status === 'pending').length}
                            prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Table */}
            <Card>
                <Table dataSource={applications} columns={columns} rowKey="id" />
            </Card>

            {/* Create App Modal */}
            <Modal
                title="Register Application"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleCreateApp} initialValues={{ integration_type: 'readonly' }}>
                    <Form.Item name="name" label="Application Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Salesforce, Jira, AWS" />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea placeholder="What is this application for?" />
                    </Form.Item>
                    <Form.Item name="owner" label="Owner" rules={[{ required: true }]}>
                        <Input placeholder="Team or person responsible" />
                    </Form.Item>
                    <Form.Item name="integration_type" label="Integration Type">
                        <Select>
                            <Select.Option value="readonly">Read-Only (Safe Mode)</Select.Option>
                            <Select.Option value="token">Token-Based</Select.Option>
                            <Select.Option value="api">Full API Integration</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>Register</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Entitlements Modal */}
            <Modal
                title={`Entitlements: ${entitlementModal?.name}`}
                open={!!entitlementModal}
                onCancel={() => setEntitlementModal(null)}
                width={700}
                footer={<Button onClick={() => setEntitlementModal(null)}>Close</Button>}
            >
                {entitlementModal && (
                    <>
                        <Table
                            dataSource={entitlementModal.entitlements}
                            columns={entitlementColumns}
                            rowKey="id"
                            size="small"
                            pagination={false}
                            style={{ marginBottom: 16 }}
                        />
                        {user?.role === 'admin' && (
                            <Card size="small" title="Add Entitlement">
                                <Form form={entitlementForm} layout="inline" onFinish={handleCreateEntitlement}>
                                    <Form.Item name="name" rules={[{ required: true }]}>
                                        <Input placeholder="Name" style={{ width: 150 }} />
                                    </Form.Item>
                                    <Form.Item name="risk_level" initialValue="low">
                                        <Select style={{ width: 100 }}>
                                            <Select.Option value="low">Low</Select.Option>
                                            <Select.Option value="medium">Medium</Select.Option>
                                            <Select.Option value="high">High</Select.Option>
                                        </Select>
                                    </Form.Item>
                                    <Form.Item name="is_privileged" valuePropName="checked" initialValue={false}>
                                        <Select style={{ width: 100 }} defaultValue={false}>
                                            <Select.Option value={false}>Normal</Select.Option>
                                            <Select.Option value={true}>Privileged</Select.Option>
                                        </Select>
                                    </Form.Item>
                                    <Form.Item>
                                        <Button type="primary" htmlType="submit" loading={submitting}>Add</Button>
                                    </Form.Item>
                                </Form>
                            </Card>
                        )}
                    </>
                )}
            </Modal>

            {/* Access Modal */}
            <Modal
                title={`Access: ${accessModal?.name}`}
                open={!!accessModal}
                onCancel={() => setAccessModal(null)}
                width={600}
                footer={<Button onClick={() => setAccessModal(null)}>Close</Button>}
            >
                {accessModal && (
                    <Table
                        dataSource={accessModal.access}
                        columns={accessColumns}
                        rowKey="id"
                        size="small"
                        pagination={false}
                    />
                )}
            </Modal>
        </div>
    );
}

export default Applications;
