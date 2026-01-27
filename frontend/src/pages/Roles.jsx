import { useState } from 'react'
import { Card, Row, Col, Tag, Typography, Space, Button, Modal, Form, Input, Select, message } from 'antd'
import { PlusOutlined, SafetyCertificateOutlined } from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography;

/**
 * Roles Page with Ant Design
 */
function Roles() {
    const [roles, setRoles] = useState([
        { id: 1, name: 'read-only', description: 'View access only', permissions: ['read'], riskLevel: 'low' },
        { id: 2, name: 'read-write', description: 'View and modify access', permissions: ['read', 'write'], riskLevel: 'medium' },
        { id: 3, name: 'admin', description: 'Full administrative access', permissions: ['read', 'write', 'delete', 'admin'], riskLevel: 'high' },
        { id: 4, name: 'developer', description: 'Development environment access', permissions: ['read', 'write', 'deploy'], riskLevel: 'medium' },
        { id: 5, name: 'auditor', description: 'Audit and compliance access', permissions: ['read', 'audit'], riskLevel: 'low' },
    ]);
    const [modalOpen, setModalOpen] = useState(false);
    const [form] = Form.useForm();

    function handleSubmit(values) {
        const newRole = {
            id: Date.now(),
            ...values,
            permissions: ['read']
        };
        setRoles([...roles, newRole]);
        setModalOpen(false);
        form.resetFields();
        message.success('Role created');
    }

    function getRiskColor(level) {
        switch (level) {
            case 'high': return 'red';
            case 'medium': return 'orange';
            default: return 'green';
        }
    }

    return (
        <div>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>Roles</Title>
                    <Text type="secondary">Define and manage access roles</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                    New Role
                </Button>
            </div>

            {/* Roles Grid */}
            <Row gutter={[16, 16]}>
                {roles.map(role => (
                    <Col xs={24} sm={12} lg={8} key={role.id}>
                        <Card hoverable>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                <Space>
                                    <SafetyCertificateOutlined style={{ color: '#1677ff' }} />
                                    <Text strong style={{ fontSize: 16 }}>{role.name}</Text>
                                </Space>
                                <Tag color={getRiskColor(role.riskLevel)}>{role.riskLevel} risk</Tag>
                            </div>
                            <Paragraph type="secondary" style={{ marginBottom: 12 }}>{role.description}</Paragraph>
                            <Space wrap>
                                {role.permissions.map(perm => (
                                    <Tag key={perm} color="blue">{perm}</Tag>
                                ))}
                            </Space>
                        </Card>
                    </Col>
                ))}
            </Row>

            {/* Create Modal */}
            <Modal
                title="Create Role"
                open={modalOpen}
                onCancel={() => setModalOpen(false)}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ riskLevel: 'low' }}>
                    <Form.Item name="name" label="Role Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., developer, viewer" />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input placeholder="What does this role do?" />
                    </Form.Item>
                    <Form.Item name="riskLevel" label="Risk Level" rules={[{ required: true }]}>
                        <Select>
                            <Select.Option value="low">Low</Select.Option>
                            <Select.Option value="medium">Medium</Select.Option>
                            <Select.Option value="high">High</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">Create</Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
}

export default Roles;
