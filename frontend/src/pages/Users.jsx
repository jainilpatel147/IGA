import { useState, useEffect } from 'react'
import {
    Card, Table, Button, Modal, Form, Input, Select, Tag, Typography,
    Space, message, Row, Col, Statistic, Tooltip, Popconfirm, Switch
} from 'antd'
import {
    PlusOutlined, UserOutlined, EditOutlined, DeleteOutlined,
    LockOutlined, CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import api from '../api/request'

const { Title, Text } = Typography

function Users() {
    const [users, setUsers] = useState([])
    const [applications, setApplications] = useState([])
    const [loading, setLoading] = useState(true)
    const [modalOpen, setModalOpen] = useState(false)
    const [editingUser, setEditingUser] = useState(null)
    const [passwordModalOpen, setPasswordModalOpen] = useState(false)
    const [selectedUser, setSelectedUser] = useState(null)
    const [form] = Form.useForm()
    const [passwordForm] = Form.useForm()
    const { user } = useAuth()

    useEffect(() => {
        fetchUsers()
        fetchApplications()
    }, [])

    async function fetchUsers() {
        try {
            setLoading(true)
            const data = await api.get('/users')
            setUsers(data)
        } catch (error) {
            message.error('Failed to load users')
        } finally {
            setLoading(false)
        }
    }

    async function fetchApplications() {
        try {
            const data = await api.get('/applications')
            setApplications(data)
        } catch (error) {
            console.error('Failed to load applications')
        }
    }

    async function handleSubmit(values) {
        try {
            if (editingUser) {
                await api.patch(`/users/${editingUser.id}`, values)
                message.success('User updated successfully')
            } else {
                await api.post('/users', values)
                message.success('User created successfully')
            }
            setModalOpen(false)
            setEditingUser(null)
            form.resetFields()
            fetchUsers()
        } catch (error) {
            message.error(error.response?.data?.detail || 'Operation failed')
        }
    }

    async function handleDelete(userId) {
        try {
            await api.delete(`/users/${userId}`)
            message.success('User deleted successfully')
            fetchUsers()
        } catch (error) {
            message.error('Failed to delete user')
        }
    }

    async function handleToggleActive(userId, isActive) {
        try {
            await api.patch(`/users/${userId}`, { is_active: !isActive })
            message.success(`User ${!isActive ? 'activated' : 'deactivated'}`)
            fetchUsers()
        } catch (error) {
            message.error('Failed to update user status')
        }
    }

    async function handleResetPassword(values) {
        try {
            await api.post(`/users/${selectedUser.id}/reset-password?new_password=${values.new_password}`)
            message.success('Password reset successfully')
            setPasswordModalOpen(false)
            setSelectedUser(null)
            passwordForm.resetFields()
        } catch (error) {
            message.error('Failed to reset password')
        }
    }

    function openEditModal(user) {
        setEditingUser(user)
        form.setFieldsValue({
            email: user.email,
            full_name: user.full_name,
            role: user.role,
            application_id: user.application_id,
            is_active: user.is_active
        })
        setModalOpen(true)
    }

    function openPasswordModal(user) {
        setSelectedUser(user)
        setPasswordModalOpen(true)
    }

    const columns = [
        {
            title: 'User',
            key: 'user',
            render: (_, record) => (
                <Space>
                    <UserOutlined style={{ fontSize: 20, color: '#1677ff' }} />
                    <div>
                        <Text strong>{record.full_name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>@{record.username}</Text>
                    </div>
                </Space>
            ),
        },
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
        },
        {
            title: 'Role',
            dataIndex: 'role',
            key: 'role',
            render: (role) => {
                const colors = { super_admin: 'red', app_admin: 'blue' }
                return <Tag color={colors[role]}>{role.replace('_', ' ').toUpperCase()}</Tag>
            },
        },
        {
            title: 'Application',
            dataIndex: 'application_name',
            key: 'application_name',
            render: (name) => name ? <Tag color="cyan">{name}</Tag> : <Text type="secondary">-</Text>,
        },
        {
            title: 'Status',
            dataIndex: 'is_active',
            key: 'is_active',
            render: (isActive) => (
                isActive ? 
                <Tag icon={<CheckCircleOutlined />} color="success">Active</Tag> :
                <Tag icon={<CloseCircleOutlined />} color="default">Inactive</Tag>
            ),
        },
        {
            title: 'Last Login',
            dataIndex: 'last_login_at',
            key: 'last_login_at',
            render: (date) => date ? new Date(date).toLocaleString() : <Text type="secondary">Never</Text>,
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Edit User">
                        <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
                    </Tooltip>
                    <Tooltip title="Reset Password">
                        <Button size="small" icon={<LockOutlined />} onClick={() => openPasswordModal(record)} />
                    </Tooltip>
                    <Tooltip title={record.is_active ? "Deactivate" : "Activate"}>
                        <Switch 
                            size="small" 
                            checked={record.is_active} 
                            onChange={() => handleToggleActive(record.id, record.is_active)}
                        />
                    </Tooltip>
                    {user?.role === 'super_admin' && (
                        <Popconfirm
                            title="Delete this user?"
                            onConfirm={() => handleDelete(record.id)}
                            okText="Yes"
                            okType="danger"
                        >
                            <Tooltip title="Delete User">
                                <Button size="small" danger icon={<DeleteOutlined />} />
                            </Tooltip>
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ]

    const activeUsers = users.filter(u => u.is_active).length
    const inactiveUsers = users.filter(u => u.is_active === false).length

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                <div>
                    <Title level={2} style={{ margin: 0 }}>User Management</Title>
                    <Text type="secondary">Manage IGA platform users</Text>
                </div>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                    setEditingUser(null)
                    form.resetFields()
                    setModalOpen(true)
                }}>
                    Add User
                </Button>
            </div>

            {/* Stats */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Total Users" value={users.length} prefix={<UserOutlined />} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Active Users"
                            value={activeUsers}
                            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                        />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic
                            title="Inactive Users"
                            value={inactiveUsers}
                            prefix={<CloseCircleOutlined style={{ color: '#d9d9d9' }} />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Table */}
            <Card>
                <Table dataSource={users} columns={columns} rowKey="id" loading={loading} />
            </Card>

            {/* Create/Edit Modal */}
            <Modal
                title={editingUser ? "Edit User" : "Add User"}
                open={modalOpen}
                onCancel={() => {
                    setModalOpen(false)
                    setEditingUser(null)
                    form.resetFields()
                }}
                footer={null}
                destroyOnClose
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit}>
                    {!editingUser && (
                        <>
                            <Form.Item name="username" label="Username" rules={[{ required: true }]}>
                                <Input placeholder="e.g., john.doe" />
                            </Form.Item>
                            <Form.Item name="password" label="Password" rules={[{ required: true }]}>
                                <Input.Password placeholder="Enter password" />
                            </Form.Item>
                        </>
                    )}
                    <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}>
                        <Input placeholder="e.g., John Doe" />
                    </Form.Item>
                    <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                        <Input placeholder="e.g., john@example.com" />
                    </Form.Item>
                    <Form.Item name="role" label="Role" rules={[{ required: true }]}>
                        <Select disabled={user?.role !== 'super_admin'}>
                            <Select.Option value="super_admin">Super Admin</Select.Option>
                            <Select.Option value="app_admin">Application Admin</Select.Option>
                        </Select>
                    </Form.Item>
                    <Form.Item 
                        noStyle 
                        shouldUpdate={(prevValues, currentValues) => prevValues.role !== currentValues.role}
                    >
                        {({ getFieldValue }) =>
                            getFieldValue('role') === 'app_admin' ? (
                                <Form.Item name="application_id" label="Application" rules={[{ required: true }]}>
                                    <Select placeholder="Select application">
                                        {applications.map(app => (
                                            <Select.Option key={app.id} value={app.id}>
                                                {app.name}
                                            </Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            ) : null
                        }
                    </Form.Item>
                    {editingUser && (
                        <Form.Item name="is_active" label="Status" valuePropName="checked">
                            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
                        </Form.Item>
                    )}
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => {
                                setModalOpen(false)
                                setEditingUser(null)
                                form.resetFields()
                            }}>
                                Cancel
                            </Button>
                            <Button type="primary" htmlType="submit">
                                {editingUser ? 'Update' : 'Create'}
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* Password Reset Modal */}
            <Modal
                title="Reset Password"
                open={passwordModalOpen}
                onCancel={() => {
                    setPasswordModalOpen(false)
                    setSelectedUser(null)
                    passwordForm.resetFields()
                }}
                footer={null}
                destroyOnClose
            >
                <Form form={passwordForm} layout="vertical" onFinish={handleResetPassword}>
                    <Text type="secondary">
                        Resetting password for: <Text strong>{selectedUser?.full_name}</Text>
                    </Text>
                    <Form.Item 
                        name="new_password" 
                        label="New Password" 
                        rules={[{ required: true, min: 6 }]}
                        style={{ marginTop: 16 }}
                    >
                        <Input.Password placeholder="Enter new password" />
                    </Form.Item>
                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => {
                                setPasswordModalOpen(false)
                                setSelectedUser(null)
                                passwordForm.resetFields()
                            }}>
                                Cancel
                            </Button>
                            <Button type="primary" htmlType="submit">
                                Reset Password
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Users
