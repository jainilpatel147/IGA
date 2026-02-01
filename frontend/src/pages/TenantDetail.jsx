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
    AuditOutlined
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
    const [idps, setIdps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('identities');

    // Modal states
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [assignRoleModalOpen, setAssignRoleModalOpen] = useState(false);
    const [selectedIdentity, setSelectedIdentity] = useState(null);
    const [identityRoles, setIdentityRoles] = useState({});
    const [form] = Form.useForm();
    const [roleForm] = Form.useForm();

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

            // Fetch identity providers
            const idpsData = await api.get(`/tenants/${tenantId}/identity-providers`);
            setIdps(idpsData);

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

    const idpColumns = [
        {
            title: 'Provider',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <KeyOutlined style={{ fontSize: 16, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        {record.is_primary && <Tag color="gold" style={{ marginLeft: 8 }}>PRIMARY</Tag>}
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'provider_type',
            key: 'provider_type',
            render: (type) => {
                const colors = { oidc: 'blue', saml: 'green', azure_ad: 'cyan', okta: 'purple', ldap: 'orange' };
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
                    error: { status: 'error', text: 'Error' },
                };
                return <Badge {...(config[status] || { status: 'default', text: status })} />;
            },
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (d) => new Date(d).toLocaleDateString(),
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
            key: 'idps',
            label: (
                <Space>
                    <KeyOutlined />
                    <span>Identity Providers ({idps.length})</span>
                </Space>
            ),
            children: idps.length > 0 ? (
                <Table
                    dataSource={idps}
                    columns={idpColumns}
                    rowKey="id"
                    pagination={false}
                />
            ) : (
                <Empty description="No identity providers configured" />
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
                            title="Identity Providers"
                            value={tenant.idp_count}
                            prefix={<KeyOutlined />}
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
        </div>
    );
}

export default TenantDetail;
