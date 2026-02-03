import { useState, useEffect } from 'react'
import { Card, Row, Col, Typography, Tag, Space, Spin, Descriptions, Alert } from 'antd'
import { CheckCircleOutlined } from '@ant-design/icons'
import api from '../api/request'

const { Title, Text } = Typography

/**
 * Connectors Page - Connector Catalog
 * Shows available connector templates
 */
function Connectors() {
    const [templates, setTemplates] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchTemplates()
    }, [])

    async function fetchTemplates() {
        try {
            const data = await api.get('/connector-templates')
            setTemplates(data)
        } catch (error) {
            console.error('Failed to load templates:', error)
        } finally {
            setLoading(false)
        }
    }

    const providerIcons = {
        microsoft: '🔷',
        okta: '🔵',
        google: '🔴',
        auth0: '🟠',
        onelogin: '🟢',
        keycloak: '🔶'
    }

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}><Spin size="large" /></div>
    }

    return (
        <div>
            <div style={{ marginBottom: 24 }}>
                <Title level={2} style={{ margin: 0 }}>Connector Catalog</Title>
                <Text type="secondary">Available SSO and provisioning connectors</Text>
            </div>

            <Alert
                message="Tenant-Specific Configuration"
                description="To configure connectors for a specific tenant, go to Applications → Select Application → Tenant → Connectors tab"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
            />

            <Row gutter={[16, 16]}>
                {templates.map(template => (
                    <Col xs={24} sm={12} lg={8} key={template.id}>
                        <Card
                            hoverable
                            style={{ height: '100%' }}
                            title={
                                <Space>
                                    <span style={{ fontSize: 24 }}>{providerIcons[template.provider] || '🔗'}</span>
                                    <span>{template.name}</span>
                                </Space>
                            }
                            extra={<Tag color="blue">{template.connector_type.toUpperCase()}</Tag>}
                        >
                            <Text type="secondary">{template.description}</Text>
                            
                            <div style={{ marginTop: 16 }}>
                                <Text strong>Capabilities:</Text>
                                <div style={{ marginTop: 8 }}>
                                    <Space wrap>
                                        {template.capabilities.map(cap => (
                                            <Tag key={cap} icon={<CheckCircleOutlined />} color="success">
                                                {cap}
                                            </Tag>
                                        ))}
                                    </Space>
                                </div>
                            </div>

                            <div style={{ marginTop: 16 }}>
                                <Text strong>Required Fields:</Text>
                                <div style={{ marginTop: 8 }}>
                                    {template.config_schema?.fields?.slice(0, 3).map(field => (
                                        <div key={field.name}>
                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                • {field.label}
                                            </Text>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </Card>
                    </Col>
                ))}
            </Row>
        </div>
    )
}

export default Connectors
