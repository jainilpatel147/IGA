import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined, SunOutlined, MoonOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const { Title, Text, Paragraph } = Typography;

/**
 * Login Page with Ant Design
 */
function Login() {
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const navigate = useNavigate();
    const [messageApi, contextHolder] = message.useMessage();

    async function handleSubmit(values) {
        setLoading(true);
        const result = await login(values.username, values.password);

        if (result.success) {
            navigate('/');
        } else {
            messageApi.error(result.error || 'Login failed');
        }
        setLoading(false);
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: isDark
                ? 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%)'
                : 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            padding: 24,
            position: 'relative',
        }}>
            {contextHolder}

            {/* Theme Toggle */}
            <Button
                type="default"
                shape="circle"
                icon={isDark ? <SunOutlined /> : <MoonOutlined />}
                onClick={toggleTheme}
                size="large"
                style={{
                    position: 'absolute',
                    top: 24,
                    right: 24,
                }}
            />

            {/* Login Card */}
            <Card
                style={{
                    width: '100%',
                    maxWidth: 400,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                }}
            >
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 32 }}>
                    <Space direction="vertical" size={8}>
                        <SafetyCertificateOutlined style={{ fontSize: 48, color: '#1677ff' }} />
                        <Title level={2} style={{ margin: 0 }}>IGA Platform</Title>
                        <Text type="secondary">Identity Governance & Administration</Text>
                    </Space>
                </div>

                {/* Login Form */}
                <Form
                    name="login"
                    onFinish={handleSubmit}
                    autoComplete="off"
                    layout="vertical"
                    size="large"
                >
                    <Form.Item
                        name="username"
                        rules={[{ required: true, message: 'Please enter username' }]}
                    >
                        <Input
                            prefix={<UserOutlined />}
                            placeholder="Username"
                        />
                    </Form.Item>

                    <Form.Item
                        name="password"
                        rules={[{ required: true, message: 'Please enter password' }]}
                    >
                        <Input.Password
                            prefix={<LockOutlined />}
                            placeholder="Password"
                        />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 16 }}>
                        <Button type="primary" htmlType="submit" block loading={loading}>
                            Sign In
                        </Button>
                    </Form.Item>
                </Form>

                {/* Demo Credentials */}
                <Card size="small" style={{ background: isDark ? '#141414' : '#f5f5f5' }}>
                    <Paragraph style={{ margin: 0, fontSize: 13 }}>
                        <Text strong>Demo Credentials:</Text>
                        <br />
                        <Text code>admin</Text> / <Text code>admin123</Text>
                        <br />
                        <Text code>user</Text> / <Text code>user123</Text>
                    </Paragraph>
                </Card>
            </Card>
        </div>
    );
}

export default Login;
