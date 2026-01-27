import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, message, Spin, Tooltip, Alert
} from 'antd'
import {
    PlusOutlined,
    KeyOutlined,
    CopyOutlined,
    DeleteOutlined,
    ReloadOutlined,
    ExclamationCircleOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography;

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API Keys Page
 * Manage API keys for external application integration
 */
function ApiKeys() {
    const [keys, setKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [newKey, setNewKey] = useState(null);
    const [form] = Form.useForm();

    useEffect(() => {
        fetchKeys();
    }, []);

    async function fetchKeys() {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api-keys`);
            const data = await res.json();
            setKeys(data);
        } catch (error) {
            console.error('Failed to load API keys:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreate(values) {
        try {
            setSubmitting(true);
            const res = await fetch(`${API_BASE}/api-keys`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: values.name,
                    scopes: values.scopes.join(','),
                    expires_in_days: values.expires_in_days || null
                })
            });

            if (!res.ok) throw new Error('Failed to create key');

            const data = await res.json();
            setNewKey(data.key);
            message.success('API key created');
            form.resetFields();
            fetchKeys();
        } catch (error) {
            message.error('Failed to create key');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleRevoke(id) {
        try {
            await fetch(`${API_BASE}/api-keys/${id}`, { method: 'DELETE' });
            message.success('API key revoked');
            fetchKeys();
        } catch (error) {
            message.error('Failed to revoke key');
        }
    }

    async function handleRotate(id) {
        try {
            const res = await fetch(`${API_BASE}/api-keys/${id}/rotate`, { method: 'POST' });
            const data = await res.json();
            setNewKey(data.key);
            message.success('API key rotated');
            fetchKeys();
        } catch (error) {
            message.error('Failed to rotate key');
        }
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text);
        message.success('Copied to clipboard');
    }

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (name) => <Text strong>{name}</Text>,
        },
        {
            title: 'Key Prefix',
            dataIndex: 'key_prefix',
            key: 'key_prefix',
            render: (prefix) => <Text code>{prefix}...</Text>,
        },
        {
            title: 'Scopes',
            dataIndex: 'scopes',
            key: 'scopes',
            render: (scopes) => (
                <Space wrap>
                    {scopes.split(',').map(s => (
                        <Tag key={s} color={s === 'admin' ? 'red' : s === 'write' ? 'orange' : 'blue'}>
                            {s}
                        </Tag>
                    ))}
                </Space>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'is_active',
            key: 'is_active',
            render: (active) => (
                <Tag color={active ? 'green' : 'default'}>{active ? 'Active' : 'Revoked'}</Tag>
            ),
        },
        {
            title: 'Last Used',
            dataIndex: 'last_used_at',
            key: 'last_used_at',
            render: (date) => date ? new Date(date).toLocaleDateString() : <Text type="secondary">Never</Text>,
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            render: (date) => date ? new Date(date).toLocaleDateString() : <Text type="secondary">Never</Text>,
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                record.is_active ? (
                    <Space>
                        <Tooltip title="Rotate key">
                            <Button size="small" icon={<ReloadOutlined />} onClick={() => handleRotate(record.id)} />
                        </Tooltip>
                        <Tooltip title="Revoke key">
                            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleRevoke(record.id)} />
                        </Tooltip>
                    </Space>
                ) : <Text type="secondary">—</Text>
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
                    <Title level={2} style={{ margin: 0 }}>API Keys</Title>
                    <Text type="secondary">Manage API keys for external application access</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    Generate Key
                </Button>
            </div>

            {/* Info Banner */}
            <Alert
                message="API Key Authentication"
                description="Use API keys to authenticate external applications. Include the key in the Authorization header: Bearer YOUR_API_KEY"
                type="info"
                showIcon
                icon={<KeyOutlined />}
                style={{ marginBottom: 16 }}
            />

            {/* New Key Display */}
            {newKey && (
                <Alert
                    message="New API Key Created"
                    description={
                        <div>
                            <Paragraph>
                                <strong>Copy this key now - it won't be shown again!</strong>
                            </Paragraph>
                            <Space>
                                <Text code copyable style={{ fontSize: 12 }}>{newKey}</Text>
                            </Space>
                        </div>
                    }
                    type="success"
                    closable
                    onClose={() => setNewKey(null)}
                    style={{ marginBottom: 16 }}
                />
            )}

            {/* Keys Table */}
            <Card>
                <Table
                    dataSource={keys}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="Generate API Key"
                open={modalOpen}
                onCancel={() => { setModalOpen(false); form.resetFields(); }}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ scopes: ['read'] }}>
                    <Form.Item name="name" label="Key Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Production App, CI/CD Pipeline" />
                    </Form.Item>

                    <Form.Item name="scopes" label="Scopes" rules={[{ required: true }]}>
                        <Select mode="multiple" placeholder="Select permissions">
                            <Select.Option value="read">Read - View identities, requests, audit</Select.Option>
                            <Select.Option value="write">Write - Create/update identities and requests</Select.Option>
                            <Select.Option value="admin">Admin - Full access including key management</Select.Option>
                        </Select>
                    </Form.Item>

                    <Form.Item name="expires_in_days" label="Expiration (days)">
                        <Select placeholder="Select expiration" allowClear>
                            <Select.Option value={30}>30 days</Select.Option>
                            <Select.Option value={90}>90 days</Select.Option>
                            <Select.Option value={180}>180 days</Select.Option>
                            <Select.Option value={365}>1 year</Select.Option>
                        </Select>
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>Generate</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default ApiKeys;
