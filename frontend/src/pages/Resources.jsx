import { useState } from 'react'
import { Card, Table, Tag, Typography, Space, Button, Modal, Form, Input, Select, message, Avatar } from 'antd'
import {
    PlusOutlined,
    DatabaseOutlined,
    CloudOutlined,
    ApiOutlined,
    AppstoreOutlined,
    GlobalOutlined,
    FolderOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography;

/**
 * Resources Page with Ant Design
 */
function Resources() {
    const [resources, setResources] = useState([
        { id: 1, name: 'production-database', type: 'database', owner: 'DBA Team', sensitivity: 'critical' },
        { id: 2, name: 'staging-environment', type: 'environment', owner: 'DevOps', sensitivity: 'high' },
        { id: 3, name: 'analytics-dashboard', type: 'application', owner: 'Data Team', sensitivity: 'medium' },
        { id: 4, name: 'payment-gateway', type: 'service', owner: 'Finance', sensitivity: 'critical' },
        { id: 5, name: 'user-api', type: 'api', owner: 'Platform Team', sensitivity: 'high' },
        { id: 6, name: 'logs-bucket', type: 'storage', owner: 'Security', sensitivity: 'medium' },
    ]);
    const [modalOpen, setModalOpen] = useState(false);
    const [form] = Form.useForm();

    function handleSubmit(values) {
        const newResource = { id: Date.now(), ...values };
        setResources([...resources, newResource]);
        setModalOpen(false);
        form.resetFields();
        message.success('Resource added');
    }

    function getTypeIcon(type) {
        const icons = {
            database: <DatabaseOutlined />,
            environment: <GlobalOutlined />,
            application: <AppstoreOutlined />,
            service: <CloudOutlined />,
            api: <ApiOutlined />,
            storage: <FolderOutlined />,
        };
        return icons[type] || <FolderOutlined />;
    }

    function getSensitivityColor(level) {
        switch (level) {
            case 'critical': return 'red';
            case 'high': return 'orange';
            case 'medium': return 'gold';
            default: return 'green';
        }
    }

    const columns = [
        {
            title: 'Resource',
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
            render: (type) => <Tag color="cyan">{type}</Tag>,
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
        },
        {
            title: 'Sensitivity',
            dataIndex: 'sensitivity',
            key: 'sensitivity',
            render: (level) => <Tag color={getSensitivityColor(level)}>{level.toUpperCase()}</Tag>,
        },
    ];

    return (
        <div>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>Resources</Title>
                    <Text type="secondary">Manage protected resources and their owners</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    New Resource
                </Button>
            </div>

            {/* Table */}
            <Card>
                <Table
                    dataSource={resources}
                    columns={columns}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* Create Modal */}
            <Modal
                title="Add Resource"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ type: 'application', sensitivity: 'medium' }}>
                    <Form.Item name="name" label="Resource Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., production-database" />
                    </Form.Item>
                    <Form.Item name="type" label="Type" rules={[{ required: true }]}>
                        <Select>
                            <Select.Option value="application">Application</Select.Option>
                            <Select.Option value="database">Database</Select.Option>
                            <Select.Option value="api">API</Select.Option>
                            <Select.Option value="service">Service</Select.Option>
                            <Select.Option value="environment">Environment</Select.Option>
                            <Select.Option value="storage">Storage</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item name="owner" label="Owner">
                        <Input placeholder="Team or person responsible" />
                    </Form.Item>
                    <Form.Item name="sensitivity" label="Sensitivity" rules={[{ required: true }]}>
                        <Select>
                            <Select.Option value="low">Low</Select.Option>
                            <Select.Option value="medium">Medium</Select.Option>
                            <Select.Option value="high">High</Select.Option>
                            <Select.Option value="critical">Critical</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">Add</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default Resources;
