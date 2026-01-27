import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, Row, Col, Segmented, Avatar, Spin, message
} from 'antd'
import {
    PlusOutlined,
    UserOutlined,
    SettingOutlined,
    CrownOutlined,
    AppstoreOutlined,
    BarsOutlined,
} from '@ant-design/icons'
import { getIdentities, createIdentity } from '../api/client'

const { Title, Text } = Typography;

/**
 * Identities Page with Ant Design
 */
function Identities() {
    const [identities, setIdentities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [viewMode, setViewMode] = useState('grid');
    const [filterType, setFilterType] = useState('all');
    const [form] = Form.useForm();

    useEffect(() => {
        fetchIdentities();
    }, []);

    async function fetchIdentities() {
        try {
            setLoading(true);
            const data = await getIdentities();
            setIdentities(data);
        } catch (error) {
            console.error('Failed to load identities:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleSubmit(values) {
        try {
            setSubmitting(true);
            await createIdentity(values);
            message.success('Identity created successfully');
            setModalOpen(false);
            form.resetFields();
            fetchIdentities();
        } catch (error) {
            message.error('Failed to create identity: ' + error.message);
        } finally {
            setSubmitting(false);
        }
    }

    function getTypeIcon(type) {
        switch (type) {
            case 'admin': return <CrownOutlined />;
            case 'service': return <SettingOutlined />;
            default: return <UserOutlined />;
        }
    }

    function getTypeColor(type) {
        switch (type) {
            case 'admin': return 'purple';
            case 'service': return 'cyan';
            default: return 'blue';
        }
    }

    // Filter identities
    const filteredIdentities = filterType === 'all'
        ? identities
        : identities.filter(i => i.type === filterType);

    const columns = [
        {
            title: 'Identity',
            key: 'name',
            render: (_, record) => (
                <Space>
                    <Avatar icon={getTypeIcon(record.type)} style={{ backgroundColor: '#1677ff' }} />
                    <Text strong>{record.name}</Text>
                </Space>
            ),
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            render: (type) => <Tag color={getTypeColor(type)}>{type.toUpperCase()}</Tag>,
        },
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            render: (id) => <Text code copyable={{ text: id }}>{id.slice(0, 8)}...</Text>,
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date) => new Date(date).toLocaleDateString(),
        },
    ];

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
                <Spin size="large" />
            </div>
        );
    }

    return (
        <div>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>Identities</Title>
                    <Text type="secondary">Manage users, services, and admin accounts</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    New Identity
                </Button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                <Segmented
                    options={[
                        { label: `All (${identities.length})`, value: 'all' },
                        { label: `Users (${identities.filter(i => i.type === 'user').length})`, value: 'user' },
                        { label: `Admins (${identities.filter(i => i.type === 'admin').length})`, value: 'admin' },
                        { label: `Services (${identities.filter(i => i.type === 'service').length})`, value: 'service' },
                    ]}
                    value={filterType}
                    onChange={setFilterType}
                />
                <Segmented
                    options={[
                        { label: <AppstoreOutlined />, value: 'grid' },
                        { label: <BarsOutlined />, value: 'list' },
                    ]}
                    value={viewMode}
                    onChange={setViewMode}
                />
            </div>

            {/* Content */}
            {viewMode === 'grid' ? (
                <Row gutter={[16, 16]}>
                    {filteredIdentities.map(identity => (
                        <Col xs={24} sm={12} lg={8} xl={6} key={identity.id}>
                            <Card hoverable>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <Space>
                                        <Avatar size={48} icon={getTypeIcon(identity.type)} style={{ backgroundColor: '#1677ff' }} />
                                        <div>
                                            <Text strong style={{ display: 'block' }}>{identity.name}</Text>
                                            <Tag color={getTypeColor(identity.type)}>{identity.type}</Tag>
                                        </div>
                                    </Space>
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        Created {new Date(identity.created_at).toLocaleDateString()}
                                    </Text>
                                </Space>
                            </Card>
                        </Col>
                    ))}
                </Row>
            ) : (
                <Card>
                    <Table
                        dataSource={filteredIdentities}
                        columns={columns}
                        rowKey="id"
                        pagination={{ pageSize: 10 }}
                    />
                </Card>
            )}

            {/* Create Modal */}
            <Modal
                title="Create Identity"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                destroyOnClose
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{ type: 'user' }}
                >
                    <Form.Item
                        name="name"
                        label="Name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                    >
                        <Input placeholder="Enter identity name" />
                    </Form.Item>

                    <Form.Item
                        name="type"
                        label="Type"
                        rules={[{ required: true }]}
                    >
                        <Select>
                            <Select.Option value="user">👤 User</Select.Option>
                            <Select.Option value="admin">👑 Admin</Select.Option>
                            <Select.Option value="service">⚙️ Service</Select.Option>
                        </Select>
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>
                                Create
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default Identities;
