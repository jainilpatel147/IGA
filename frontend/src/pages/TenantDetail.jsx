import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
    Card, Table, Button, Typography, Space, Tag, Spin, Descriptions,
    Row, Col, Statistic, Badge, Breadcrumb, Empty, Tabs, Modal, Form,
    Input, Select, message, Popconfirm, Tooltip
} from 'antd'
import {
    TeamOutlined,
    UserOutlined,
    SafetyCertificateOutlined,
    KeyOutlined,
    ArrowLeftOutlined,
    LockOutlined,
    PlusOutlined,
    DeleteOutlined,
    UserAddOutlined,
    AppstoreOutlined,
    AuditOutlined,
    SyncOutlined,
    EyeOutlined,
    LinkOutlined,
    CloudSyncOutlined
} from '@ant-design/icons'
import api from '../api/request'
import { useAuth } from '../context/AuthContext'

const { Title, Text } = Typography;
const { Option } = Select;

/**
 * Tenant Detail Page
 * Shows tenant info with its identities, roles, entitlements, and identity providers
 */
function TenantDetail() {
    const { appId, tenantId } = useParams();
    const navigate = useNavigate();
    const { user, token } = useAuth();

    const [tenant, setTenant] = useState(null);
    const [identities, setIdentities] = useState([]);
    const [roles, setRoles] = useState([]);
    const [entitlements, setEntitlements] = useState([]);
    const [connectors, setConnectors] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('identities');

    // Modal states
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [assignRoleModalOpen, setAssignRoleModalOpen] = useState(false);
    const [connectorModalOpen, setConnectorModalOpen] = useState(false);
    const [connectorDetailsModal, setConnectorDetailsModal] = useState(null);
    const [selectedIdentity, setSelectedIdentity] = useState(null);
    const [identityRoles, setIdentityRoles] = useState({});
    const [testing, setTesting] = useState(null);
    const [form] = Form.useForm();
    const [roleForm] = Form.useForm();
    const [connectorForm] = Form.useForm();
    const [syncing, setSyncing] = useState(null);

    useEffect(() => {
        fetchData();
    }, [tenantId]);

    async function fetchData() {
        try {
            setLoading(true);

            // Fetch tenant details
            const tenantData = await api.get(`/tenants/${tenantId}`);
            setTenant(tenantData);

            // Fetch identities
            const identitiesData = await api.get(`/tenants/${tenantId}/identities`);
            setIdentities(identitiesData);

            // Fetch roles
            const rolesData = await api.get(`/tenants/${tenantId}/roles`);
            setRoles(rolesData);

            // Fetch entitlements (from Application scope)
            const entData = await api.get(`/applications/${appId}/entitlements`);
            setEntitlements(entData);

            // Fetch tenant connectors
            const connectorsData = await api.get(`/tenants/${tenantId}/connectors`);
            setConnectors(connectorsData);

            // Fetch connector templates
            const templatesData = await api.get('/connector-templates');
            setTemplates(templatesData);

            // Fetch roles for each identity
            const rolesMap = {};
            for (const identity of identitiesData) {
                try {
                    const roles = await api.get(`/tenants/${tenantId}/identities/${identity.id}/roles`);
                    rolesMap[identity.id] = roles;
                } catch (e) {
                    rolesMap[identity.id] = [];
                }
            }
            setIdentityRoles(rolesMap);

        } catch (error) {
            console.error('Failed to load tenant:', error);
            message.error('Failed to load tenant data');
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateIdentity(values) {
        try {
            await api.post(`/tenants/${tenantId}/identities`, values);

            message.success('Identity created successfully');
            setCreateModalOpen(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            message.error(error.message);
        }
    }

    async function handleDeleteIdentity(identityId) {
        try {
            await api.delete(`/tenants/${tenantId}/identities/${identityId}`);

            message.success('Identity deactivated');
            fetchData();
        } catch (error) {
            message.error(error.message);
        }
    }

    async function handleAssignRole(values) {
        try {
            await api.post(`/tenants/${tenantId}/identities/${selectedIdentity.id}/roles`, values);

            message.success('Role assigned successfully');
            setAssignRoleModalOpen(false);
            roleForm.resetFields();
            fetchData();
        } catch (error) {
            message.error(error.message);
        }
    }

    async function handleRevokeRole(identityId, roleId) {
        try {
            await api.delete(`/tenants/${tenantId}/identities/${identityId}/roles/${roleId}`);

            message.success('Role revoked');
            fetchData();
        } catch (error) {
            message.error(error.message);
        }
    }

    async function handleCreateConnector(values) {
        try {
            const template = templates.find(t => t.id === values.template_id);

            if (!template) {
                message.error('Selected connector template not found');
                return;
            }

            const config = {};
            template.config_schema.fields.forEach(field => {
                if (values[field.name]) {
                    config[field.name] = values[field.name];
                }
            });

            // Validate all required fields are present
            const missingFields = template.config_schema.fields
                .filter(f => f.required && !config[f.name])
                .map(f => f.label);

            if (missingFields.length > 0) {
                message.error(`Missing required fields: ${missingFields.join(', ')}`);
                return;
            }

            await api.post(`/tenants/${tenantId}/connectors`, {
                template_id: values.template_id,
                config
            });

            message.success('Connector configured successfully');
            setConnectorModalOpen(false);
            connectorForm.resetFields();
            fetchData();
        } catch (error) {
            console.error('Connector creation error:', error);
            message.error(error.message || 'Failed to create connector');
        }
    }

    async function handleTestConnector(connectorId) {
        try {
            setTesting(connectorId);
            const data = await api.post(`/tenants/${tenantId}/connectors/${connectorId}/test`);

            if (data.success) {
                message.success('Connection successful');
            } else {
                message.error(data.message);
            }
            fetchData();
        } catch (error) {
            message.error('Connection test failed');
        } finally {
            setTesting(null);
        }
    }

    const handleDeleteConnector = async (connectorId) => {
        try {
            await api.delete(`/tenants/${tenantId}/connectors/${connectorId}`);
            message.success('Connector deleted successfully');
            fetchData();
        } catch (error) {
            message.error('Failed to delete connector');
        }
    }

    const handleSyncIdentities = async (connectorId) => {
        setSyncing(connectorId);
        try {
            const response = await api.post(`/tenants/${tenantId}/connectors/${connectorId}/sync-identities`);
            message.success(response.data.message);
            fetchData();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Identity sync failed';
            message.error(errorMsg);
        } finally {
            setSyncing(null);
        }
    }

    const handleSyncResources = async (connectorId) => {
        setSyncing(connectorId);
        try {
            const response = await api.post(`/tenants/${tenantId}/connectors/${connectorId}/sync-resources`);
            message.success(response.data.message);
            fetchData();
        } catch (error) {
            const errorMsg = error.response?.data?.detail || 'Resource sync failed';
            message.error(errorMsg);
        } finally {
            setSyncing(null);
        }
    }

    async function showConnectorDetails(connectorId) {
        try {
            const data = await api.get(`/tenants/${tenantId}/connectors/${connectorId}`);
            setConnectorDetailsModal(data);
        } catch (error) {
            message.error('Failed to load details');
        }
    }

    function openAssignRoleModal(identity) {
        setSelectedIdentity(identity);
        setAssignRoleModalOpen(true);
    }

    const identityColumns = [
        {
            title: 'Name',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <UserOutlined style={{ fontSize: 16, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.email}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'identity_type',
            key: 'identity_type',
            render: (type) => {
                const colors = { user: 'blue', service: 'purple', admin: 'red' };
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
                    suspended: { status: 'error', text: 'Suspended' },
                };
                return <Badge {...(config[status] || { status: 'default', text: status })} />;
            },
        },
        {
            title: 'Roles',
            key: 'roles',
            render: (_, record) => {
                const assignedRoles = identityRoles[record.id] || [];
                if (assignedRoles.length === 0) {
                    return <Text type="secondary">No roles</Text>;
                }
                return (
                    <Space wrap size={[0, 4]}>
                        {assignedRoles.map(r => (
                            <Tag
                                key={r.id}
                                color={r.is_privileged ? 'red' : 'green'}
                                closable
                                onClose={(e) => {
                                    e.preventDefault();
                                    handleRevokeRole(record.id, r.role_id);
                                }}
                            >
                                {r.role_display_name || r.role_name}
                            </Tag>
                        ))}
                    </Space>
                );
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Assign Role">
                        <Button
                            size="small"
                            icon={<SafetyCertificateOutlined />}
                            onClick={() => openAssignRoleModal(record)}
                            disabled={record.status !== 'active'}
                        >
                            Assign Role
                        </Button>
                    </Tooltip>
                    <Popconfirm
                        title="Deactivate this identity?"
                        description="The identity will be marked as inactive."
                        onConfirm={() => handleDeleteIdentity(record.id)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Tooltip title="Deactivate">
                            <Button
                                size="small"
                                danger
                                icon={<DeleteOutlined />}
                                disabled={record.status === 'inactive'}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    const roleColumns = [
        {
            title: 'Role',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <SafetyCertificateOutlined style={{ fontSize: 16, color: record.is_privileged ? '#ff4d4f' : '#52c41a' }} />
                    <div>
                        <Text strong>{record.display_name || record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Risk Level',
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
            render: (priv) => priv ? <Tag color="red" icon={<LockOutlined />}>PRIVILEGED</Tag> : <Tag>STANDARD</Tag>,
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (d) => new Date(d).toLocaleDateString(),
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

    const connectorColumns = [
        {
            title: 'Connector',
            key: 'name',
            render: (_, record) => {
                const providerIcons = {
                    microsoft: '🔷',
                    okta: '🔵',
                    google: '🔴',
                    auth0: '🟠',
                    onelogin: '🟢',
                    keycloak: '🔶'
                };
                return (
                    <Space>
                        <span style={{ fontSize: 20 }}>{providerIcons[record.provider] || '🔗'}</span>
                        <div>
                            <Text strong>{record.template_name}</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>{record.provider}</Text>
                        </div>
                    </Space>
                );
            },
        },
        {
            title: 'Type',
            dataIndex: 'connector_type',
            key: 'connector_type',
            render: (type) => <Tag color="blue">{type.toUpperCase()}</Tag>,
        },
        {
            title: 'Category',
            dataIndex: 'category',
            key: 'category',
            render: (category) => {
                const colors = {
                    SSO: 'purple',
                    APPLICATION: 'orange',
                    DIRECTORY: 'cyan',
                    CLOUD: 'blue'
                };
                return <Tag color={colors[category] || 'default'}>{category}</Tag>;
            },
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status, record) => {
                const config = {
                    active: { status: 'success', text: 'Active' },
                    inactive: { status: 'default', text: 'Inactive' },
                    error: { status: 'error', text: 'Error' },
                    pending: { status: 'warning', text: 'Pending' },
                };
                const badge = config[status] || { status: 'default', text: status };
                return (
                    <div>
                        <Badge status={badge.status} text={badge.text} />
                        {!record.is_enabled && <Tag color="red" style={{ marginLeft: 8 }}>Disabled</Tag>}
                    </div>
                );
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
                    <Tooltip title="View Details">
                        <Button
                            size="small"
                            icon={<AuditOutlined />}
                            onClick={() => showConnectorDetails(record.id)}
                        />
                    </Tooltip>
                    <Tooltip title="Test Connection">
                        <Button
                            size="small"
                            icon={<SyncOutlined spin={testing === record.id} />}
                            onClick={() => handleTestConnector(record.id)}
                            loading={testing === record.id}
                        />
                    </Tooltip>
                    {record.category === 'SSO' && (
                        <Tooltip title="Sync Identities">
                            <Button
                                size="small"
                                icon={<CloudSyncOutlined />}
                                onClick={() => handleSyncIdentities(record.id)}
                                loading={syncing === record.id}
                                disabled={!record.is_enabled}
                            />
                        </Tooltip>
                    )}
                    {(record.category === 'APPLICATION' || record.category === 'CLOUD') && (
                        <Tooltip title="Sync Roles & Entitlements">
                            <Button
                                size="small"
                                icon={<CloudSyncOutlined />}
                                onClick={() => handleSyncResources(record.id)}
                                loading={syncing === record.id}
                                disabled={!record.is_enabled}
                            />
                        </Tooltip>
                    )}
                    <Popconfirm
                        title="Delete this connector?"
                        onConfirm={() => handleDeleteConnector(record.id)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Tooltip title="Delete">
                            <Button size="small" danger icon={<DeleteOutlined />} />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    const tabItems = [
        {
            key: 'identities',
            label: (
                <Space>
                    <UserOutlined />
                    <span>Identities ({identities.length})</span>
                </Space>
            ),
            children: (
                <div>
                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                            type="primary"
                            icon={<UserAddOutlined />}
                            onClick={() => setCreateModalOpen(true)}
                        >
                            Create Identity
                        </Button>
                    </div>
                    {identities.length > 0 ? (
                        <Table
                            dataSource={identities}
                            columns={identityColumns}
                            rowKey="id"
                            pagination={{ pageSize: 10 }}
                        />
                    ) : (
                        <Empty description="No identities in this tenant">
                            <Button type="primary" onClick={() => setCreateModalOpen(true)}>
                                Create First Identity
                            </Button>
                        </Empty>
                    )}
                </div>
            ),
        },
        {
            key: 'roles',
            label: (
                <Space>
                    <SafetyCertificateOutlined />
                    <span>Roles ({roles.length})</span>
                </Space>
            ),
            children: roles.length > 0 ? (
                <Table
                    dataSource={roles}
                    columns={roleColumns}
                    rowKey="id"
                    pagination={false}
                />
            ) : (
                <Empty description="No roles defined for this tenant" />
            ),
        },
        {
            key: 'entitlements',
            label: (
                <Space>
                    <AppstoreOutlined />
                    <span>Entitlements ({entitlements.length})</span>
                </Space>
            ),
            children: entitlements.length > 0 ? (
                <Table
                    dataSource={entitlements}
                    columns={entitlementColumns}
                    rowKey="id"
                    pagination={false}
                />
            ) : (
                <Empty description="No entitlements defined for this application" />
            ),
        },
        {
            key: 'connectors',
            label: (
                <Space>
                    <LinkOutlined />
                    <span>Connectors ({connectors.length})</span>
                </Space>
            ),
            children: (
                <div>
                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => setConnectorModalOpen(true)}
                        >
                            Configure Connector
                        </Button>
                    </div>
                    {connectors.length > 0 ? (
                        <Table
                            dataSource={connectors}
                            columns={connectorColumns}
                            rowKey="id"
                            pagination={false}
                        />
                    ) : (
                        <Empty description="No connectors configured for this tenant">
                            <Button type="primary" onClick={() => setConnectorModalOpen(true)}>
                                Configure First Connector
                            </Button>
                        </Empty>
                    )}
                </div>
            ),
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    if (!tenant) {
        return <Empty description="Tenant not found" />;
    }

    // Get available roles (roles not yet assigned to selected identity)
    const getAvailableRoles = () => {
        if (!selectedIdentity) return roles;
        const assignedRoleIds = (identityRoles[selectedIdentity.id] || []).map(r => r.role_id);
        return roles.filter(r => !assignedRoleIds.includes(r.id));
    };

    return (
        <div>
            {/* Breadcrumb */}
            <Breadcrumb style={{ marginBottom: 16 }}>
                <Breadcrumb.Item>
                    <Link to="/applications">Applications</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item>
                    <Link to={`/applications/${appId}`}>{tenant.application_name}</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item>{tenant.name}</Breadcrumb.Item>
            </Breadcrumb>

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate(`/applications/${appId}`)}
                    />
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <TeamOutlined style={{ marginRight: 12, color: '#1677ff' }} />
                            {tenant.name}
                        </Title>
                        <Text type="secondary">{tenant.description || `Tenant: ${tenant.slug}`}</Text>
                    </div>
                </div>
                <Space>
                    <Tag color={tenant.tenant_type === 'customer' ? 'green' : 'blue'}>
                        {tenant.tenant_type.toUpperCase()}
                    </Tag>
                    {tenant.is_default && <Tag color="purple">DEFAULT TENANT</Tag>}
                    <Badge
                        status={tenant.status === 'active' ? 'success' : 'warning'}
                        text={tenant.status.toUpperCase()}
                    />
                </Space>
            </div>

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Identities"
                            value={tenant.identity_count}
                            prefix={<UserOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Roles"
                            value={tenant.role_count}
                            prefix={<SafetyCertificateOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Entitlements"
                            value={entitlements.length}
                            prefix={<AppstoreOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Connectors"
                            value={connectors.length}
                            prefix={<LinkOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Tenant Details */}
            <Card title="Tenant Details" style={{ marginBottom: 24 }}>
                <Descriptions column={2}>
                    <Descriptions.Item label="ID">{tenant.id}</Descriptions.Item>
                    <Descriptions.Item label="Slug">{tenant.slug}</Descriptions.Item>
                    <Descriptions.Item label="Type">
                        <Tag color={tenant.tenant_type === 'customer' ? 'green' : 'blue'}>
                            {tenant.tenant_type.toUpperCase()}
                        </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Status">
                        <Badge status={tenant.status === 'active' ? 'success' : 'warning'} text={tenant.status} />
                    </Descriptions.Item>
                    <Descriptions.Item label="Default Tenant">
                        {tenant.is_default ? 'Yes' : 'No'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Created">{new Date(tenant.created_at).toLocaleString()}</Descriptions.Item>
                </Descriptions>
            </Card>

            {/* Tabs: Identities, Roles, Entitlements, IdPs */}
            <Card>
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={tabItems}
                />
            </Card>

            {/* Create Identity Modal */}
            <Modal
                title="Create New Identity"
                open={createModalOpen}
                onCancel={() => {
                    setCreateModalOpen(false);
                    form.resetFields();
                }}
                footer={null}
            >
                <Form form={form} layout="vertical" onFinish={handleCreateIdentity}>
                    <Form.Item
                        name="name"
                        label="Name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                    >
                        <Input placeholder="John Doe" />
                    </Form.Item>
                    <Form.Item
                        name="email"
                        label="Email"
                        rules={[{ type: 'email', message: 'Please enter a valid email' }]}
                    >
                        <Input placeholder="john.doe@example.com" />
                    </Form.Item>
                    <Form.Item
                        name="identity_type"
                        label="Identity Type"
                        initialValue="user"
                    >
                        <Select>
                            <Option value="user">User</Option>
                            <Option value="service">Service Account</Option>
                            <Option value="admin">Administrator</Option>
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="external_id"
                        label="External ID (SSO)"
                    >
                        <Input placeholder="Optional SSO identifier" />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">Create</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Assign Role Modal */}
            <Modal
                title={`Assign Role to ${selectedIdentity?.name}`}
                open={assignRoleModalOpen}
                onCancel={() => {
                    setAssignRoleModalOpen(false);
                    roleForm.resetFields();
                    setSelectedIdentity(null);
                }}
                footer={null}
            >
                <Form form={roleForm} layout="vertical" onFinish={handleAssignRole}>
                    <Form.Item
                        name="role_id"
                        label="Select Role"
                        rules={[{ required: true, message: 'Please select a role' }]}
                    >
                        <Select placeholder="Choose a role to assign" emptyMessage="No roles available">
                            {getAvailableRoles().length > 0 ? getAvailableRoles().map(role => (
                                <Option key={role.id} value={role.id}>
                                    <Space>
                                        {role.display_name || role.name}
                                        {role.is_privileged && <Tag color="red" size="small">PRIVILEGED</Tag>}
                                        <Tag color={role.risk_level === 'high' ? 'red' : role.risk_level === 'medium' ? 'orange' : 'green'}>
                                            {role.risk_level}
                                        </Tag>
                                    </Space>
                                </Option>
                            )) : <Option disabled>No roles available. Please create a role first.</Option>}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="justification"
                        label="Justification"
                    >
                        <Input.TextArea placeholder="Reason for assigning this role (optional)" rows={3} />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setAssignRoleModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">Assign Role</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Configure Connector Modal */}
            <Modal
                title="Configure Connector"
                open={connectorModalOpen}
                onCancel={() => {
                    setConnectorModalOpen(false);
                    connectorForm.resetFields();
                }}
                footer={null}
                width={600}
            >
                <Form form={connectorForm} layout="vertical" onFinish={(values) => {
                    // Custom handling for Generic REST Application
                    // We need to bundle the individual fields back into the JSON structure expected by the backend
                    if (values.template_id) {
                        const template = templates.find(t => t.id === values.template_id);
                        if (template && template.slug === 'generic-rest-app') {
                            const connection = {
                                base_url: values.base_url,
                                auth_type: values.auth_type,
                                timeout_seconds: 30,
                                retry_count: 3,
                                auth_config: {}
                            };

                            if (values.auth_type === 'API_KEY') {
                                connection.auth_config = {
                                    header_name: values.api_key_header,
                                    header_value: values.api_key_value
                                };
                            } else if (values.auth_type === 'BASIC') {
                                connection.auth_config = {
                                    username: values.basic_username,
                                    password: values.basic_password
                                };
                            } else if (values.auth_type === 'OAUTH2') {
                                connection.auth_config = {
                                    token_url: values.oauth_token_url,
                                    client_id: values.oauth_client_id,
                                    client_secret: values.oauth_client_secret,
                                    scope: values.oauth_scope
                                };
                            }

                            const endpoints = [
                                {
                                    operation: 'FETCH_ROLES',
                                    method: 'GET',
                                    path: values.roles_endpoint,
                                    enabled: !!values.roles_endpoint
                                },
                                {
                                    operation: 'FETCH_ENTITLEMENTS',
                                    method: 'GET',
                                    path: values.entitlements_endpoint,
                                    enabled: !!values.entitlements_endpoint
                                }
                            ];

                            const response_mapping = {};
                            if (values.roles_endpoint) {
                                response_mapping['FETCH_ROLES'] = {
                                    root_path: values.roles_root_path,
                                    id_field: values.roles_id_field || 'id',
                                    name_field: values.roles_name_field || 'name',
                                    description_field: values.roles_desc_field
                                };
                            }
                            if (values.entitlements_endpoint) {
                                response_mapping['FETCH_ENTITLEMENTS'] = {
                                    root_path: values.entitlements_root_path,
                                    id_field: values.entitlements_id_field || 'id',
                                    name_field: values.entitlements_name_field || 'name',
                                    description_field: values.entitlements_desc_field
                                };
                            }

                            // Overwrite the flat values with the structured JSON
                            values.connection = connection;
                            values.endpoints = endpoints;
                            values.response_mapping = response_mapping;
                        }
                    }
                    handleCreateConnector(values);
                }}>
                    <Form.Item name="category_filter" label="Connector Category">
                        <Select
                            placeholder="All Categories"
                            allowClear
                            onChange={() => connectorForm.setFieldsValue({ template_id: undefined })}
                        >
                            <Select.Option value="SSO">SSO</Select.Option>
                            <Select.Option value="APPLICATION">Application</Select.Option>
                            <Select.Option value="DIRECTORY">Directory</Select.Option>
                            <Select.Option value="CLOUD">Cloud Infrastructure</Select.Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        noStyle
                        shouldUpdate={(prev, curr) => prev.category_filter !== curr.category_filter}
                    >
                        {({ getFieldValue }) => {
                            const category = getFieldValue('category_filter');
                            const filteredTemplates = category
                                ? templates.filter(t => t.category === category)
                                : templates;

                            return (
                                <Form.Item
                                    name="template_id"
                                    label="Connector Template"
                                    rules={[{ required: true, message: 'Please select a connector template' }]}
                                >
                                    <Select placeholder="Select connector template">
                                        {filteredTemplates.map(t => (
                                            <Select.Option key={t.id} value={t.id}>
                                                <Space>
                                                    {t.name}
                                                    <Tag style={{ marginLeft: 8 }} color={
                                                        t.category === 'SSO' ? 'purple' :
                                                            t.category === 'APPLICATION' ? 'orange' :
                                                                t.category === 'DIRECTORY' ? 'cyan' : 'blue'
                                                    }>
                                                        {t.category}
                                                    </Tag>
                                                </Space>
                                            </Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            );
                        }}
                    </Form.Item>

                    <Form.Item noStyle shouldUpdate={(prev, curr) => prev.template_id !== curr.template_id}>
                        {() => {
                            const templateId = connectorForm.getFieldValue('template_id');
                            const template = templates.find(t => t.id === templateId);

                            if (!template) return null;

                            // Special handling for Generic REST Application
                            if (template.slug === 'generic-rest-app') {
                                return (
                                    <>
                                        <Card type="inner" title="Connection Settings" size="small" style={{ marginBottom: 16 }}>
                                            <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
                                                <Input placeholder="https://api.example.com" />
                                            </Form.Item>
                                            <Form.Item name="auth_type" label="Authentication Type" initialValue="NONE">
                                                <Select>
                                                    <Select.Option value="NONE">None</Select.Option>
                                                    <Select.Option value="API_KEY">API Key</Select.Option>
                                                    <Select.Option value="BASIC">Basic Auth</Select.Option>
                                                    <Select.Option value="OAUTH2">OAuth2 (Client Creds)</Select.Option>
                                                </Select>
                                            </Form.Item>

                                            <Form.Item noStyle shouldUpdate={(prev, curr) => prev.auth_type !== curr.auth_type}>
                                                {({ getFieldValue }) => {
                                                    const authType = getFieldValue('auth_type');
                                                    if (authType === 'API_KEY') {
                                                        return (
                                                            <Space style={{ display: 'flex' }} align="start">
                                                                <Form.Item name="api_key_header" label="Header Name" rules={[{ required: true }]}>
                                                                    <Input placeholder="Authorization" />
                                                                </Form.Item>
                                                                <Form.Item name="api_key_value" label="Value" rules={[{ required: true }]}>
                                                                    <Input.Password placeholder="Bearer <token>" />
                                                                </Form.Item>
                                                            </Space>
                                                        );
                                                    }
                                                    if (authType === 'BASIC') {
                                                        return (
                                                            <Space style={{ display: 'flex' }} align="start">
                                                                <Form.Item name="basic_username" label="Username" rules={[{ required: true }]}>
                                                                    <Input />
                                                                </Form.Item>
                                                                <Form.Item name="basic_password" label="Password" rules={[{ required: true }]}>
                                                                    <Input.Password />
                                                                </Form.Item>
                                                            </Space>
                                                        );
                                                    }
                                                    if (authType === 'OAUTH2') {
                                                        return (
                                                            <>
                                                                <Form.Item name="oauth_token_url" label="Token URL" rules={[{ required: true }]}>
                                                                    <Input placeholder="https://auth.example.com/token" />
                                                                </Form.Item>
                                                                <Space style={{ display: 'flex' }} align="start">
                                                                    <Form.Item name="oauth_client_id" label="Client ID" rules={[{ required: true }]}>
                                                                        <Input />
                                                                    </Form.Item>
                                                                    <Form.Item name="oauth_client_secret" label="Client Secret" rules={[{ required: true }]}>
                                                                        <Input.Password />
                                                                    </Form.Item>
                                                                </Space>
                                                                <Form.Item name="oauth_scope" label="Scope">
                                                                    <Input placeholder="read:users" />
                                                                </Form.Item>
                                                            </>
                                                        );
                                                    }
                                                    return null;
                                                }}
                                            </Form.Item>
                                        </Card>

                                        <Card type="inner" title="Operations & Mapping" size="small">
                                            <Tabs size="small" items={[
                                                {
                                                    key: 'roles',
                                                    label: 'Fetch Roles',
                                                    children: (
                                                        <>
                                                            <Form.Item name="roles_endpoint" label="Roles Endpoint (Path)">
                                                                <Input placeholder="/v1/roles" />
                                                            </Form.Item>
                                                            <Space size="small">
                                                                <Form.Item name="roles_root_path" label="Root JSON Path">
                                                                    <Input placeholder="data.items" />
                                                                </Form.Item>
                                                                <Form.Item name="roles_id_field" label="ID Field">
                                                                    <Input placeholder="id" />
                                                                </Form.Item>
                                                                <Form.Item name="roles_name_field" label="Name Field">
                                                                    <Input placeholder="name" />
                                                                </Form.Item>
                                                            </Space>
                                                        </>
                                                    )
                                                },
                                                {
                                                    key: 'entitlements',
                                                    label: 'Fetch Entitlements',
                                                    children: (
                                                        <>
                                                            <Form.Item name="entitlements_endpoint" label="Entitlements Endpoint (Path)">
                                                                <Input placeholder="/v1/permissions" />
                                                            </Form.Item>
                                                            <Space size="small">
                                                                <Form.Item name="entitlements_root_path" label="Root JSON Path">
                                                                    <Input placeholder="data" />
                                                                </Form.Item>
                                                                <Form.Item name="entitlements_id_field" label="ID Field">
                                                                    <Input placeholder="id" />
                                                                </Form.Item>
                                                                <Form.Item name="entitlements_name_field" label="Name Field">
                                                                    <Input placeholder="code" />
                                                                </Form.Item>
                                                            </Space>
                                                        </>
                                                    )
                                                }
                                            ]} />
                                        </Card>
                                    </>
                                );
                            }

                            // Default Generic Form for other templates
                            return template.config_schema.fields.map(field => (
                                <Form.Item
                                    key={field.name}
                                    name={field.name}
                                    label={field.label}
                                    rules={[{ required: field.required, message: `${field.label} is required` }]}
                                >
                                    {field.type === 'password' ? (
                                        <Input.Password placeholder={field.placeholder} />
                                    ) : field.type === 'select' ? (
                                        <Select>
                                            {field.options && field.options.map(opt => (
                                                <Select.Option key={opt} value={opt}>{opt}</Select.Option>
                                            ))}
                                        </Select>
                                    ) : (
                                        <Input placeholder={field.placeholder} />
                                    )}
                                </Form.Item>
                            ));
                        }}
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setConnectorModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">Configure</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Connector Details Modal */}
            <Modal
                title="Connector Details"
                open={!!connectorDetailsModal}
                onCancel={() => setConnectorDetailsModal(null)}
                footer={<Button onClick={() => setConnectorDetailsModal(null)}>Close</Button>}
                width={600}
            >
                {connectorDetailsModal && (
                    <Descriptions column={1} bordered>
                        <Descriptions.Item label="Connector">{connectorDetailsModal.template_name}</Descriptions.Item>
                        <Descriptions.Item label="Provider">{connectorDetailsModal.provider}</Descriptions.Item>
                        <Descriptions.Item label="Type">{connectorDetailsModal.connector_type}</Descriptions.Item>
                        <Descriptions.Item label="Status">
                            <Badge
                                status={connectorDetailsModal.status === 'active' ? 'success' : 'warning'}
                                text={connectorDetailsModal.status}
                            />
                        </Descriptions.Item>
                        <Descriptions.Item label="Configuration">
                            {Object.entries(connectorDetailsModal.config || {}).map(([key, value]) => (
                                <div key={key}>
                                    <Text strong>{key}:</Text> {value}
                                </div>
                            ))}
                        </Descriptions.Item>
                        <Descriptions.Item label="Last Sync">
                            {connectorDetailsModal.last_sync_at ? new Date(connectorDetailsModal.last_sync_at).toLocaleString() : 'Never'}
                        </Descriptions.Item>
                        {connectorDetailsModal.sync_stats && Object.keys(connectorDetailsModal.sync_stats).length > 0 && (
                            <Descriptions.Item label="Sync Stats">
                                {Object.entries(connectorDetailsModal.sync_stats).map(([key, value]) => (
                                    <div key={key}>
                                        <Text>{key}: {value}</Text>
                                    </div>
                                ))}
                            </Descriptions.Item>
                        )}
                    </Descriptions>
                )}
            </Modal>
        </div>
    );
}

export default TenantDetail;
