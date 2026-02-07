import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
    Card, Table, Button, Typography, Space, Tag, Spin, Descriptions,
    Row, Col, Statistic, Badge, Breadcrumb, Empty, Progress, Tabs, Popconfirm, Tooltip
} from 'antd'
import {
    AppstoreOutlined,
    TeamOutlined,
    SafetyCertificateOutlined,
    CloudOutlined,
    DesktopOutlined,
    ArrowLeftOutlined,
    AuditOutlined,
    PlusOutlined,
    ApiOutlined,
    SearchOutlined,
    DeleteOutlined,
} from '@ant-design/icons'
import api from '../api/request'
import { message, Modal, Form, Input } from 'antd'
import ApplicationConnectors from '../components/ApplicationConnectors'
import TenantDiscovery from '../components/TenantDiscovery'

const { Title, Text } = Typography;

/**
 * Application Detail Page
 * Shows application info with tabs for tenants, connectors, discovery, and reviews
 */
function ApplicationDetail() {
    const { appId } = useParams();
    const navigate = useNavigate();

    const [application, setApplication] = useState(null);
    const [tenants, setTenants] = useState([]);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isAddTenantModalVisible, setIsAddTenantModalVisible] = useState(false);
    const [activeTab, setActiveTab] = useState('tenants');
    const [form] = Form.useForm();

    useEffect(() => {
        fetchData();
    }, [appId]);

    async function fetchData() {
        try {
            setLoading(true);

            // Fetch app details
            const appData = await api.get(`/applications/${appId}`);
            setApplication(appData);

            // Fetch tenants
            const tenantData = await api.get(`/tenants/by-application/${appId}`);
            setTenants(tenantData);

            // Fetch access reviews
            const reviewData = await api.get('/access-reviews');
            setReviews(reviewData);

        } catch (error) {
            console.error('Failed to load application:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateTenant(values) {
        try {
            await api.post('/tenants', {
                application_id: appId,
                ...values,
                tenant_type: application.deployment_type === 'cloud' ? 'customer' : 'default'
            });
            message.success('Tenant created successfully');
            setIsAddTenantModalVisible(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            console.error('Failed to create tenant:', error);
            message.error(error.message || 'Failed to create tenant');
        }
    }

    async function handleDeleteTenant(tenantId) {
        try {
            await api.delete(`/tenants/${tenantId}`);
            message.success('Tenant deleted successfully');
            fetchData();
        } catch (error) {
            message.error('Failed to delete tenant');
        }
    }

    const tenantColumns = [
        {
            title: 'Tenant',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <TeamOutlined style={{ fontSize: 18, color: '#1677ff' }} />
                    <div>
                        <Link to={`/applications/${appId}/tenants/${record.id}`}>
                            <Text strong style={{ cursor: 'pointer' }}>{record.name}</Text>
                        </Link>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.slug}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'tenant_type',
            key: 'tenant_type',
            render: (type) => {
                const colors = { default: 'blue', customer: 'green' };
                return <Tag color={colors[type]}>{type?.toUpperCase()}</Tag>;
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
                    pending: { status: 'warning', text: 'Pending' },
                };
                return <Badge {...(config[status] || { status: 'default', text: status })} />;
            },
        },
        {
            title: 'Onboarding',
            dataIndex: 'onboarding_status',
            key: 'onboarding_status',
            render: (status) => {
                if (!status || status === 'manually_created') return null;
                const config = {
                    pending_onboarding: { color: 'warning', text: 'Pending' },
                    approved: { color: 'success', text: 'Approved' },
                    rejected: { color: 'error', text: 'Rejected' },
                };
                const cfg = config[status] || { color: 'default', text: status };
                return <Tag color={cfg.color}>{cfg.text}</Tag>;
            },
        },
        {
            title: 'Default',
            dataIndex: 'is_default',
            key: 'is_default',
            render: (isDefault) => isDefault ? <Tag color="purple">DEFAULT</Tag> : null,
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (d) => new Date(d).toLocaleDateString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        onClick={() => navigate(`/applications/${appId}/tenants/${record.id}`)}
                    >
                        View Details
                    </Button>
                    <Popconfirm
                        title="Delete this tenant?"
                        description="This will delete all identities, roles, and data in this tenant."
                        onConfirm={() => handleDeleteTenant(record.id)}
                        okText="Yes, Delete"
                        okType="danger"
                        cancelText="Cancel"
                    >
                        <Tooltip title="Delete Tenant">
                            <Button size="small" danger icon={<DeleteOutlined />} />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    const reviewColumns = [
        {
            title: 'Campaign',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <AuditOutlined style={{ fontSize: 16, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const colors = { draft: 'default', active: 'processing', completed: 'success', cancelled: 'error' };
                return <Tag color={colors[status]}>{status?.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Progress',
            key: 'progress',
            render: (_, record) => {
                const completed = record.certified_count + record.revoked_count;
                const percent = record.total_items ? Math.round((completed / record.total_items) * 100) : 0;
                return (
                    <Space direction="vertical" size={0} style={{ width: 120 }}>
                        <Progress percent={percent} size="small" />
                        <Text type="secondary" style={{ fontSize: 11 }}>
                            {completed}/{record.total_items} reviewed
                        </Text>
                    </Space>
                );
            },
        },
    ];

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>;
    }

    if (!application) {
        return <Empty description="Application not found" />;
    }

    const isCloud = application.deployment_type === 'cloud';
    const activeReviews = reviews.filter(r => r.status === 'active');

    const tabItems = [
        {
            key: 'tenants',
            label: (
                <Space>
                    <TeamOutlined />
                    Tenants ({tenants.length})
                </Space>
            ),
            children: (
                <Card
                    title={
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                            <Space>
                                <TeamOutlined />
                                <span>Tenants ({tenants.length})</span>
                            </Space>
                            {application.can_add_tenant !== false && (application.deployment_type === 'cloud' || tenants.length === 0) && (
                                <Button
                                    type="primary"
                                    icon={<PlusOutlined />}
                                    size="small"
                                    onClick={() => setIsAddTenantModalVisible(true)}
                                >
                                    Add Tenant
                                </Button>
                            )}
                        </div>
                    }
                >
                    {tenants.length > 0 ? (
                        <Table
                            dataSource={tenants}
                            columns={tenantColumns}
                            rowKey="id"
                            pagination={false}
                        />
                    ) : (
                        <Empty description="No tenants configured" />
                    )}
                </Card>
            ),
        },
        {
            key: 'connectors',
            label: (
                <Space>
                    <ApiOutlined />
                    Connectors
                    {isCloud && <Tag color="blue" size="small">Discovery</Tag>}
                </Space>
            ),
            children: (
                <ApplicationConnectors applicationId={appId} isCloud={isCloud} />
            ),
        },
        {
            key: 'discovery',
            label: (
                <Space>
                    <SearchOutlined />
                    Tenant Discovery
                </Space>
            ),
            children: (
                <TenantDiscovery applicationId={appId} isCloud={isCloud} />
            ),
        },
        {
            key: 'reviews',
            label: (
                <Space>
                    <AuditOutlined />
                    Access Reviews ({reviews.length})
                </Space>
            ),
            children: (
                <Card
                    title={
                        <Space>
                            <AuditOutlined />
                            <span>Access Reviews ({reviews.length})</span>
                        </Space>
                    }
                    extra={<Link to="/access-reviews">Manage Reviews</Link>}
                >
                    {reviews.length > 0 ? (
                        <Table
                            dataSource={reviews}
                            columns={reviewColumns}
                            rowKey="id"
                            pagination={false}
                        />
                    ) : (
                        <Empty description="No access reviews found" />
                    )}
                </Card>
            ),
        },
    ];

    return (
        <div>
            {/* Breadcrumb */}
            <Breadcrumb style={{ marginBottom: 16 }}>
                <Breadcrumb.Item>
                    <Link to="/applications">Applications</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item>{application.name}</Breadcrumb.Item>
            </Breadcrumb>

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <Button
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate('/applications')}
                    />
                    <div>
                        <Title level={2} style={{ margin: 0 }}>
                            <AppstoreOutlined style={{ marginRight: 12, color: '#1677ff' }} />
                            {application.name}
                        </Title>
                        <Text type="secondary">{application.description}</Text>
                    </div>
                </div>
                <Space>
                    {isCloud ? (
                        <Tag icon={<CloudOutlined />} color="blue">CLOUD (Multi-Tenant)</Tag>
                    ) : (
                        <Tag icon={<DesktopOutlined />} color="purple">ON-PREMISE (Single Tenant)</Tag>
                    )}
                    <Badge status={application.status === 'active' ? 'success' : 'warning'} text={application.status?.toUpperCase()} />
                </Space>
            </div>

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Tenants"
                            value={tenants.length}
                            prefix={<TeamOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Active Reviews"
                            value={activeReviews.length}
                            prefix={<SafetyCertificateOutlined />}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Owner"
                            value={application.owner}
                            valueStyle={{ fontSize: 16 }}
                        />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic
                            title="Integration"
                            value={application.integration_type?.toUpperCase()}
                            valueStyle={{ fontSize: 16 }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Application Details */}
            <Card title="Application Details" style={{ marginBottom: 24 }}>
                <Descriptions column={2}>
                    <Descriptions.Item label="ID">{application.id}</Descriptions.Item>
                    <Descriptions.Item label="Deployment Type">
                        {isCloud ? 'Cloud (Multi-Tenant SaaS)' : 'On-Premise (Single Tenant)'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Integration Type">{application.integration_type}</Descriptions.Item>
                    <Descriptions.Item label="Status">
                        <Badge status={application.status === 'active' ? 'success' : 'warning'} text={application.status} />
                    </Descriptions.Item>
                    <Descriptions.Item label="Created">{new Date(application.created_at).toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label="Owner">{application.owner}</Descriptions.Item>
                </Descriptions>
            </Card>

            {/* Tabbed Content */}
            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={tabItems}
                size="large"
            />

            {/* Add Tenant Modal */}
            <Modal
                title="Add New Tenant"
                open={isAddTenantModalVisible}
                onCancel={() => {
                    setIsAddTenantModalVisible(false);
                    form.resetFields();
                }}
                onOk={() => form.submit()}
                destroyOnClose
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreateTenant}
                    initialValues={{
                        status: 'active'
                    }}
                >
                    <Form.Item
                        name="name"
                        label="Tenant Name"
                        rules={[{ required: true, message: 'Please enter tenant name' }]}
                    >
                        <Input placeholder="Acme Corp" />
                    </Form.Item>
                    <Form.Item
                        name="slug"
                        label="Slug (Optional)"
                        extra="URL-friendly identifier. Will be generated from name if left blank."
                    >
                        <Input placeholder="acme-corp" />
                    </Form.Item>
                    <Form.Item
                        name="description"
                        label="Description"
                    >
                        <Input.TextArea placeholder="Enter tenant description" rows={3} />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default ApplicationDetail;

