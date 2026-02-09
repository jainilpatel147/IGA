import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, Segmented, Checkbox, message, Spin, Popconfirm
} from 'antd'
import {
    PlusOutlined,
    CheckOutlined,
    CloseOutlined,
    WarningOutlined,
} from '@ant-design/icons'
import {
    getAccessRequests,
    getIdentities,
    createAccessRequest,
    approveRequest,
    rejectRequest
} from '../api/client'

const { Title, Text } = Typography;

/**
 * Access Requests Page with Ant Design
 */
function AccessRequests({ tenantId, identities: propIdentities }) {
    const [requests, setRequests] = useState([]);
    const [identities, setIdentities] = useState([]);
    const [loading, setLoading] = useState(true);
    // ...
    useEffect(() => {
        fetchData();
    }, [tenantId, propIdentities]);

    async function fetchData() {
        try {
            setLoading(true);
            const requestsPromise = getAccessRequests(null, tenantId);
            // If propIdentities is provided and has items, use it. Otherwise fetch.
            // But if propIdentities is [], it might just be not loaded yet.
            // We should rely on parent to pass updated list.
            const identitiesPromise = (propIdentities && propIdentities.length > 0)
                ? Promise.resolve(propIdentities)
                : getIdentities();

            const [requestsData, identitiesData] = await Promise.all([
                requestsPromise,
                identitiesPromise
            ]);
            setRequests(requestsData);
            if (identitiesData) {
                setIdentities(identitiesData);
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleSubmit(values) {
        try {
            setSubmitting(true);
            await createAccessRequest(values);
            message.success('Access request submitted');
            setModalOpen(false);
            form.resetFields();
            fetchData();
        } catch (error) {
            message.error('Failed to create request: ' + error.message);
        } finally {
            setSubmitting(false);
        }
    }

    async function handleApprove(id) {
        try {
            await approveRequest(id, 'Approved via dashboard');
            message.success('Request approved');
            fetchData();
        } catch (error) {
            message.error('Failed to approve');
        }
    }

    async function handleReject(id) {
        try {
            await rejectRequest(id, 'Rejected via dashboard');
            message.success('Request rejected');
            fetchData();
        } catch (error) {
            message.error('Failed to reject');
        }
    }

    async function handleBulkApprove() {
        for (const id of selectedRowKeys) {
            try {
                await approveRequest(id, 'Bulk approved');
            } catch (e) { }
        }
        message.success(`${selectedRowKeys.length} requests approved`);
        setSelectedRowKeys([]);
        fetchData();
    }

    async function handleBulkReject() {
        for (const id of selectedRowKeys) {
            try {
                await rejectRequest(id, 'Bulk rejected');
            } catch (e) { }
        }
        message.success(`${selectedRowKeys.length} requests rejected`);
        setSelectedRowKeys([]);
        fetchData();
    }

    function getIdentityName(id) {
        const identity = identities.find(i => i.id === id);
        return identity?.name || id.slice(0, 8) + '...';
    }

    function getRiskLevel(request) {
        const highRiskRoles = ['admin', 'write', 'delete', 'root'];
        const highRiskResources = ['production', 'payment', 'finance'];

        if (highRiskRoles.some(r => request.role.toLowerCase().includes(r)) ||
            highRiskResources.some(r => request.resource.toLowerCase().includes(r))) {
            return { level: 'high', color: 'red' };
        }
        if (request.role.toLowerCase().includes('read')) {
            return { level: 'low', color: 'green' };
        }
        return { level: 'medium', color: 'orange' };
    }

    const filteredRequests = filter === 'all'
        ? requests
        : requests.filter(r => r.status === filter);

    const pendingCount = requests.filter(r => r.status === 'pending').length;

    const columns = [
        {
            title: 'Identity',
            dataIndex: 'identity_id',
            key: 'identity_id',
            render: (id, record) => {
                // Check if this is an identity creation request
                if (record.extra_data?.request_type === 'identity_creation') {
                    const data = record.extra_data.identity_data || {};
                    return (
                        <Space direction="vertical" size={0}>
                            <Text strong>{data.name}</Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>{data.email} ({data.identity_type})</Text>
                            <Tag color="cyan" style={{ marginTop: 4 }}>New Identity</Tag>
                        </Space>
                    );
                }
                // Regular access request
                return <Text strong>{getIdentityName(id)}</Text>;
            },
        },
        {
            title: 'Resource',
            dataIndex: 'resource',
            key: 'resource',
            render: (text, record) => {
                if (record.extra_data?.request_type === 'identity_creation') {
                    return <Text type="secondary">Identity Platform</Text>;
                }
                return text;
            }
        },
        {
            title: 'Role',
            dataIndex: 'role',
            key: 'role',
            render: (role, record) => {
                if (record.extra_data?.request_type === 'identity_creation') {
                    const type = record.extra_data.identity_data?.identity_type || 'user';
                    return <Tag color="blue">{type.toUpperCase()}</Tag>;
                }
                return <Text code>{role}</Text>;
            }
        },
        {
            title: 'Risk',
            key: 'risk',
            render: (_, record) => {
                const risk = getRiskLevel(record);
                return <Tag color={risk.color}>{risk.level.toUpperCase()}</Tag>;
            },
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const colors = { pending: 'orange', approved: 'green', rejected: 'red' };
                return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
            },
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
                record.status === 'pending' ? (
                    <Space>
                        <Popconfirm title="Approve this request?" onConfirm={() => handleApprove(record.id)}>
                            <Button type="primary" size="small" icon={<CheckOutlined />}>Approve</Button>
                        </Popconfirm>
                        <Popconfirm title="Reject this request?" onConfirm={() => handleReject(record.id)}>
                            <Button danger size="small" icon={<CloseOutlined />}>Reject</Button>
                        </Popconfirm>
                    </Space>
                ) : <Text type="secondary">—</Text>
            ),
        },
    ];

    const rowSelection = {
        selectedRowKeys,
        onChange: setSelectedRowKeys,
        getCheckboxProps: (record) => ({
            disabled: record.status !== 'pending',
        }),
    };

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
                    <Title level={2} style={{ margin: 0 }}>Access Requests</Title>
                    <Text type="secondary">Review and manage access requests</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    New Request
                </Button>
            </div>

            {/* Filters */}
            <Segmented
                options={[
                    { label: 'All', value: 'all' },
                    { label: `Pending (${pendingCount})`, value: 'pending' },
                    { label: 'Approved', value: 'approved' },
                    { label: 'Rejected', value: 'rejected' },
                ]}
                value={filter}
                onChange={setFilter}
                style={{ marginBottom: 16 }}
            />

            {/* Bulk Actions */}
            {selectedRowKeys.length > 0 && (
                <Card size="small" style={{ marginBottom: 16, background: '#e6f7ff', borderColor: '#1677ff' }}>
                    <Space>
                        <Text strong>{selectedRowKeys.length} selected</Text>
                        <Button type="primary" size="small" onClick={handleBulkApprove}>Approve All</Button>
                        <Button danger size="small" onClick={handleBulkReject}>Reject All</Button>
                        <Button size="small" onClick={() => setSelectedRowKeys([])}>Clear</Button>
                    </Space>
                </Card>
            )}

            {/* Table */}
            <Card>
                <Table
                    dataSource={filteredRequests}
                    columns={columns}
                    rowKey="id"
                    rowSelection={rowSelection}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="Request Access"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit}>
                    <Form.Item
                        name="identity_id"
                        label="Identity"
                        rules={[{ required: true, message: 'Select an identity' }]}
                    >
                        <Select placeholder="Select identity">
                            {identities.map(i => (
                                <Select.Option key={i.id} value={i.id}>
                                    {i.name} ({i.type})
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="resource"
                        label="Resource"
                        rules={[{ required: true, message: 'Enter resource' }]}
                    >
                        <Input placeholder="e.g., production-database" />
                    </Form.Item>

                    <Form.Item
                        name="role"
                        label="Role"
                        rules={[{ required: true, message: 'Enter role' }]}
                    >
                        <Input placeholder="e.g., read-only, admin" />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit" loading={submitting}>Submit</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default AccessRequests;
