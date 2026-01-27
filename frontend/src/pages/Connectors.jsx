import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, message, Spin, Tooltip, Badge, Descriptions
} from 'antd'
import {
    PlusOutlined,
    ApiOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    SyncOutlined,
    DeleteOutlined,
    SettingOutlined,
    CloudOutlined,
    SafetyOutlined,
    LinkOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography;

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Connectors Page
 * Manage external application connectors
 */
function Connectors() {
    const [connectors, setConnectors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [testing, setTesting] = useState(null);
    const [form] = Form.useForm();

    useEffect(() => {
        fetchConnectors();
    }, []);

    async function fetchConnectors() {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/connectors`);
            const data = await res.json();
            setConnectors(data);
        } catch (error) {
            console.error('Failed to load connectors:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreate(values) {
        try {
            setSubmitting(true);
            const res = await fetch(`${API_BASE}/connectors`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: values.name,
                    description: values.description,
                    connector_type: values.connector_type,
                    config: {
                        base_url: values.base_url,
                        client_id: values.client_id,
                        client_secret: values.client_secret,
                    }
                })
            });

            if (!res.ok) throw new Error('Failed to create connector');

            message.success('Connector created');
            setModalOpen(false);
            form.resetFields();
            fetchConnectors();
        } catch (error) {
            message.error('Failed to create connector');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleTest(id) {
        try {
            setTesting(id);
            const res = await fetch(`${API_BASE}/connectors/${id}/test`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                message.success('Connection successful');
            } else {
                message.error(data.message);
            }
            fetchConnectors();
        } catch (error) {
            message.error('Connection test failed');
        } finally {
            setTesting(null);
        }
    }

    async function handleDelete(id) {
        try {
            await fetch(`${API_BASE}/connectors/${id}`, { method: 'DELETE' });
            message.success('Connector deleted');
            fetchConnectors();
        } catch (error) {
            message.error('Failed to delete connector');
        }
    }

    function getTypeIcon(type) {
        const icons = {
            oauth2: <SafetyOutlined />,
            scim: <SyncOutlined />,
            api: <ApiOutlined />,
            ldap: <LinkOutlined />,
            saml: <SafetyOutlined />,
        };
        return icons[type] || <CloudOutlined />;
    }

    function getStatusBadge(status) {
        const config = {
            active: { status: 'success', text: 'Active' },
            inactive: { status: 'default', text: 'Inactive' },
            error: { status: 'error', text: 'Error' },
            pending: { status: 'warning', text: 'Pending' },
        };
        return config[status] || { status: 'default', text: status };
    }

    const columns = [
        {
            title: 'Connector',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <span style={{ fontSize: 20 }}>{getTypeIcon(record.connector_type)}</span>
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'connector_type',
            key: 'connector_type',
            render: (type) => <Tag color="blue">{type.toUpperCase()}</Tag>,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const badge = getStatusBadge(status);
                return <Badge status={badge.status} text={badge.text} />;
            },
        },
        {
            title: 'Last Sync',
            dataIndex: 'last_sync_at',
            key: 'last_sync_at',
            render: (date) => date ? new Date(date).toLocaleString() : <Text type="secondary">Never</Text>,
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Test connection">
                        <Button
                            size="small"
                            icon={<SyncOutlined spin={testing === record.id} />}
                            onClick={() => handleTest(record.id)}
                            loading={testing === record.id}
                        >
                            Test
                        </Button>
                    </Tooltip>
                    <Tooltip title="Delete">
                        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
                    </Tooltip>
                </Space>
            ),
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>Connectors</Title>
                    <Text type="secondary">Connect external applications for SSO and provisioning</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    Add Connector
                </Button>
            </div>

            {/* Connector Types Info */}
            <Card size="small" style={{ marginBottom: 16 }}>
                <Space size="large" wrap>
                    <Space><SafetyOutlined /> <Text>OAuth2/OIDC - SSO</Text></Space>
                    <Space><SyncOutlined /> <Text>SCIM - User Provisioning</Text></Space>
                    <Space><ApiOutlined /> <Text>API - Custom Integration</Text></Space>
                    <Space><LinkOutlined /> <Text>LDAP - Directory Sync</Text></Space>
                </Space>
            </Card>

            {/* Connectors Table */}
            <Card>
                <Table
                    dataSource={connectors}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="Add Connector"
                open={modalOpen}
                onCancel={() => { setModalOpen(false); form.resetFields(); }}
                footer={null}
                destroyOnClose
                width={600}
            >
                <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ connector_type: 'oauth2' }}>
                    <Form.Item name="name" label="Connector Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Okta SSO, Azure AD" />
                    </Form.Item>

                    <Form.Item name="description" label="Description">
                        <Input placeholder="What is this connector for?" />
                    </Form.Item>

                    <Form.Item name="connector_type" label="Type" rules={[{ required: true }]}>
                        <Select>
                            <Select.Option value="oauth2">OAuth2/OIDC - Single Sign-On</Select.Option>
                            <Select.Option value="scim">SCIM 2.0 - User Provisioning</Select.Option>
                            <Select.Option value="api">Custom API</Select.Option>
                            <Select.Option value="ldap">LDAP - Directory</Select.Option>
                            <Select.Option value="saml">SAML 2.0 - SSO</Select.Option>
                        </Select>
                    </Form.Item>

                    <Form.Item name="base_url" label="Base URL">
                        <Input placeholder="https://your-app.com" />
                    </Form.Item>

                    <Form.Item name="client_id" label="Client ID">
                        <Input placeholder="OAuth client ID or API key" />
                    </Form.Item>

                    <Form.Item name="client_secret" label="Client Secret">
                        <Input.Password placeholder="OAuth client secret" />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>Create</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default Connectors;
