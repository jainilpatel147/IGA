import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
    Card, Table, Button, Typography, Space, Tag, Spin, Descriptions,
    Row, Col, Statistic, Badge, Breadcrumb, Empty, Progress
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
} from '@ant-design/icons'
import api from '../api/request'
import { message, Modal, Form, Input } from 'antd'

const { Title, Text } = Typography;

/**
 * Application Detail Page
 * Shows application info with list of tenants and access reviews
 */
function ApplicationDetail() {
    const { appId } = useParams();
    const navigate = useNavigate();

    const [application, setApplication] = useState(null);
    const [tenants, setTenants] = useState([]);
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isAddTenantModalVisible, setIsAddTenantModalVisible] = useState(false);
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
            // Ideally backend would support ?application_id=... but for now we fetch all
            // and filter if needed, or rely on the fact that reviews target resources
            // associated with this app. For this implementation, we just show all reviews.
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
                <Button
                    type="primary"
                    size="small"
                    onClick={() => navigate(`/applications/${appId}/tenants/${record.id}`)}
                >
                    View Details
                </Button>
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
                return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
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
                    <Badge status={application.status === 'active' ? 'success' : 'warning'} text={application.status.toUpperCase()} />
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
                            value={application.integration_type.toUpperCase()}
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

            {/* Tenants Table */}
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
                style={{ marginBottom: 24 }}
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

            {/* Access Reviews Table */}
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
