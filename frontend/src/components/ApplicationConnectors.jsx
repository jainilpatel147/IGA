/**
 * Application Connectors Component
 * Manages application-level connectors for tenant discovery
 * 
 * KEY ARCHITECTURAL POINTS:
 * - Application connectors are for TENANT DISCOVERY only
 * - SSO connectors cannot be used for discovery
 * - Only works with APPLICATION-scoped templates
 */

import { useState, useEffect } from 'react';
import {
    Card, Table, Button, Space, Tag, Empty, Badge, Modal,
    Form, Input, Select, message, Typography, Tooltip, Spin
} from 'antd';
import {
    ApiOutlined, PlusOutlined, SyncOutlined,
    CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import api from '../api/request';

const { Text } = Typography;
const { Option } = Select;

function ApplicationConnectors({ applicationId, isCloud }) {
    const [connectors, setConnectors] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [creating, setCreating] = useState(false);
    const [form] = Form.useForm();

    useEffect(() => {
        fetchData();
    }, [applicationId]);

    async function fetchData() {
        try {
            setLoading(true);

            // Fetch application connectors
            const connectorData = await api.get(`/applications/${applicationId}/connectors`);
            setConnectors(connectorData.connectors || []);

            // Fetch discovery-capable templates
            const templateData = await api.get('/applications/connector-templates/discovery');
            setTemplates(templateData.templates || []);
        } catch (error) {
            console.error('Failed to load connectors:', error);
            message.error('Failed to load connectors');
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateConnector(values) {
        try {
            setCreating(true);

            // Parse custom_headers if present
            const payload = { ...values };
            if (payload.config && payload.config.custom_headers) {
                try {
                    payload.config.custom_headers = JSON.parse(payload.config.custom_headers);
                } catch (e) {
                    message.error('Invalid JSON format for custom headers');
                    setCreating(false);
                    return;
                }
            }

            await api.post(`/applications/${applicationId}/connectors`, payload);
            message.success('Application connector created successfully');
            setIsModalVisible(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            console.error('Failed to create connector:', error);
            message.error(error.message || 'Failed to create connector');
        } finally {
            setCreating(false);
        }
    }

    async function handleTriggerDiscovery(connectorId) {
        try {
            await api.post(`/applications/${applicationId}/discover-tenants`, {
                connector_id: connectorId
            });
            message.success('Tenant discovery started');
            fetchData();
        } catch (error) {
            console.error('Discovery failed:', error);
            message.error(error.message || 'Failed to trigger discovery');
        }
    }

    const columns = [
        {
            title: 'Connector',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <ApiOutlined style={{ fontSize: 18, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            ID: {record.id?.substring(0, 8)}...
                        </Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const config = {
                    active: { color: 'success', icon: <CheckCircleOutlined /> },
                    pending: { color: 'warning', icon: <ExclamationCircleOutlined /> },
                    error: { color: 'error', icon: <CloseCircleOutlined /> },
                };
                const cfg = config[status] || { color: 'default' };
                return <Tag color={cfg.color} icon={cfg.icon}>{status?.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Enabled',
            dataIndex: 'is_enabled',
            key: 'is_enabled',
            render: (enabled) => (
                <Badge status={enabled ? 'success' : 'default'} text={enabled ? 'Yes' : 'No'} />
            ),
        },
        {
            title: 'Last Discovery',
            dataIndex: 'last_discovery_at',
            key: 'last_discovery_at',
            render: (date) => date ? new Date(date).toLocaleString() : 'Never',
        },
        {
            title: 'Stats',
            dataIndex: 'discovery_stats',
            key: 'discovery_stats',
            render: (stats) => stats?.total_tenants_discovered ? (
                <Tooltip title={`Created: ${stats.tenants_created}, Updated: ${stats.tenants_updated}`}>
                    <Tag color="blue">{stats.total_tenants_discovered} tenants</Tag>
                </Tooltip>
            ) : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        icon={<SyncOutlined />}
                        onClick={() => handleTriggerDiscovery(record.id)}
                        disabled={!record.is_enabled}
                    >
                        Discover Tenants
                    </Button>
                </Space>
            ),
        },
    ];

    const selectedTemplate = Form.useWatch('template_id', form);
    const templateConfig = templates.find(t => t.id === selectedTemplate)?.config_schema?.fields || [];

    if (loading) {
        return <Spin />;
    }

    return (
        <div>
            <Card
                title={
                    <Space>
                        <ApiOutlined />
                        <span>Application Connectors</span>
                        <Tag color="blue">For Tenant Discovery</Tag>
                    </Space>
                }
                extra={
                    isCloud && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => setIsModalVisible(true)}
                        >
                            Add Connector
                        </Button>
                    )
                }
            >
                {!isCloud ? (
                    <Empty
                        description={
                            <span>
                                Application connectors are only available for<br />
                                <strong>Cloud (Multi-Tenant)</strong> applications
                            </span>
                        }
                    />
                ) : connectors.length > 0 ? (
                    <Table
                        dataSource={connectors}
                        columns={columns}
                        rowKey="id"
                        pagination={false}
                    />
                ) : (
                    <Empty description="No application connectors configured">
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => setIsModalVisible(true)}
                        >
                            Add First Connector
                        </Button>
                    </Empty>
                )}
            </Card>

            {/* Create Connector Modal */}
            <Modal
                title="Create Application Connector"
                open={isModalVisible}
                onCancel={() => {
                    setIsModalVisible(false);
                    form.resetFields();
                }}
                onOk={() => form.submit()}
                confirmLoading={creating}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreateConnector}
                >
                    <Form.Item
                        name="template_id"
                        label="Connector Template"
                        rules={[{ required: true, message: 'Select a template' }]}
                    >
                        <Select placeholder="Select discovery-capable template">
                            {templates.map(t => (
                                <Option key={t.id} value={t.id}>
                                    <Space>
                                        <span>{t.name}</span>
                                        <Tag color="green" size="small">{t.category}</Tag>
                                    </Space>
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="name"
                        label="Connector Name"
                        rules={[{ required: true, message: 'Enter connector name' }]}
                    >
                        <Input placeholder="e.g., GitHub Enterprise Discovery" />
                    </Form.Item>

                    {templateConfig.length > 0 && (
                        <Card title="Configuration" size="small" style={{ marginBottom: 16 }}>
                            {templateConfig.map(field => (
                                <Form.Item
                                    key={field.name}
                                    name={['config', field.name]}
                                    label={field.label || field.name}
                                    rules={field.required ? [{ required: true, message: `${field.label} is required` }] : []}
                                >
                                    {field.type === 'password' ? (
                                        <Input.Password placeholder={field.placeholder || `Enter ${field.label}`} />
                                    ) : (
                                        <Input
                                            placeholder={field.placeholder || field.default || `Enter ${field.label}`}
                                        />
                                    )}
                                </Form.Item>
                            ))}

                            <Form.Item
                                name={['config', 'custom_headers']}
                                label="Custom Headers (Optional)"
                                tooltip="Add extra HTTP headers as JSON"
                            >
                                <Input.TextArea
                                    placeholder='{"X-Custom-Header": "value"}'
                                    rows={2}
                                />
                            </Form.Item>
                        </Card>
                    )}
                </Form>
            </Modal>
        </div>
    );
}

export default ApplicationConnectors;
