import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, message, Spin, Progress, Tooltip, DatePicker, Popconfirm
} from 'antd'
import {
    PlusOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    PlayCircleOutlined,
    EyeOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography;

const API_BASE = 'http://localhost:8000';

/**
 * Access Reviews Page
 * Periodic access certification campaigns
 */
function AccessReviews() {
    const [reviews, setReviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [detailsModal, setDetailsModal] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [form] = Form.useForm();

    useEffect(() => {
        fetchReviews();
    }, []);

    async function fetchReviews() {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/access-reviews`);
            const data = await res.json();
            setReviews(data);
        } catch (error) {
            console.error('Failed to load reviews:', error);
        } finally {
            setLoading(false);
        }
    }

    async function fetchReviewDetails(id) {
        try {
            const res = await fetch(`${API_BASE}/access-reviews/${id}`);
            const data = await res.json();
            setDetailsModal(data);
        } catch (error) {
            message.error('Failed to load review details');
        }
    }

    async function handleCreate(values) {
        try {
            setSubmitting(true);
            const res = await fetch(`${API_BASE}/access-reviews`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: values.name,
                    description: values.description,
                    resource_filter: values.resource_filter,
                    end_date: values.end_date?.toISOString()
                })
            });

            if (!res.ok) throw new Error('Failed to create review');

            message.success('Access review created');
            setModalOpen(false);
            form.resetFields();
            fetchReviews();
        } catch (error) {
            message.error('Failed to create review');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleStart(id) {
        try {
            await fetch(`${API_BASE}/access-reviews/${id}/start`, { method: 'POST' });
            message.success('Review started');
            fetchReviews();
        } catch (error) {
            message.error('Failed to start review');
        }
    }

    async function handleDecision(reviewId, itemId, decision) {
        try {
            await fetch(`${API_BASE}/access-reviews/${reviewId}/items/${itemId}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision })
            });
            message.success(`Access ${decision}`);
            fetchReviewDetails(reviewId);
            fetchReviews();
        } catch (error) {
            message.error('Failed to save decision');
        }
    }

    const columns = [
        {
            title: 'Campaign',
            key: 'name',
            render: (_, record) => (
                <div>
                    <Text strong>{record.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.description}</Text>
                </div>
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
        {
            title: 'Certified',
            dataIndex: 'certified_count',
            key: 'certified_count',
            render: (count) => <Tag color="green">{count}</Tag>,
        },
        {
            title: 'Revoked',
            dataIndex: 'revoked_count',
            key: 'revoked_count',
            render: (count) => <Tag color="red">{count}</Tag>,
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date) => new Date(date).toLocaleDateString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    {record.status === 'draft' && (
                        <Tooltip title="Start review">
                            <Button size="small" type="primary" icon={<PlayCircleOutlined />} onClick={() => handleStart(record.id)}>
                                Start
                            </Button>
                        </Tooltip>
                    )}
                    <Tooltip title="View details">
                        <Button size="small" icon={<EyeOutlined />} onClick={() => fetchReviewDetails(record.id)}>
                            Review
                        </Button>
                    </Tooltip>
                </Space>
            ),
        },
    ];

    const itemColumns = [
        {
            title: 'Identity',
            dataIndex: 'identity_name',
            key: 'identity_name',
            render: (name) => <Text strong>{name}</Text>,
        },
        {
            title: 'Resource',
            dataIndex: 'resource',
            key: 'resource',
        },
        {
            title: 'Role',
            dataIndex: 'role',
            key: 'role',
            render: (role) => <Text code>{role}</Text>,
        },
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
            title: 'Decision',
            key: 'decision',
            render: (_, record) => {
                if (record.decision) {
                    return (
                        <Tag
                            color={record.decision === 'certified' ? 'green' : 'red'}
                            icon={record.decision === 'certified' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                        >
                            {record.decision.toUpperCase()}
                        </Tag>
                    );
                }
                return <Tag>PENDING</Tag>;
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                !record.decision && detailsModal?.status === 'active' ? (
                    <Space>
                        <Popconfirm
                            title="Certify this access?"
                            onConfirm={() => handleDecision(detailsModal.id, record.id, 'certified')}
                        >
                            <Button size="small" type="primary" icon={<CheckCircleOutlined />}>Certify</Button>
                        </Popconfirm>
                        <Popconfirm
                            title="Revoke this access?"
                            onConfirm={() => handleDecision(detailsModal.id, record.id, 'revoked')}
                        >
                            <Button size="small" danger icon={<CloseCircleOutlined />}>Revoke</Button>
                        </Popconfirm>
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
                    <Title level={2} style={{ margin: 0 }}>Access Reviews</Title>
                    <Text type="secondary">Periodic certification of user access rights</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    New Campaign
                </Button>
            </div>

            {/* Reviews Table */}
            <Card>
                <Table
                    dataSource={reviews}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="Create Access Review Campaign"
                open={modalOpen}
                onCancel={() => { setModalOpen(false); form.resetFields(); }}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleCreate}>
                    <Form.Item name="name" label="Campaign Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Q1 2025 Access Review" />
                    </Form.Item>

                    <Form.Item name="description" label="Description">
                        <Input placeholder="Describe the review scope" />
                    </Form.Item>

                    <Form.Item name="resource_filter" label="Resource Filter">
                        <Input placeholder="Filter by resource name (e.g., production)" />
                    </Form.Item>

                    <Form.Item name="end_date" label="Due Date">
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>Create</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Details Modal */}
            <Modal
                title={detailsModal?.name || 'Review Details'}
                open={!!detailsModal}
                onCancel={() => setDetailsModal(null)}
                width={900}
                footer={<Button onClick={() => setDetailsModal(null)}>Close</Button>}
            >
                {detailsModal && (
                    <>
                        <Space style={{ marginBottom: 16 }}>
                            <Tag color={detailsModal.status === 'active' ? 'processing' : 'default'}>
                                {detailsModal.status.toUpperCase()}
                            </Tag>
                            <Text>
                                {detailsModal.certified_count} certified, {detailsModal.revoked_count} revoked,
                                {detailsModal.total_items - detailsModal.certified_count - detailsModal.revoked_count} pending
                            </Text>
                        </Space>
                        <Table
                            dataSource={detailsModal.items}
                            columns={itemColumns}
                            rowKey="id"
                            size="small"
                            pagination={{ pageSize: 5 }}
                        />
                    </>
                )}
            </Modal>
        </div>
    );
}

export default AccessReviews;
