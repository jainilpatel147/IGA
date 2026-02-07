/**
 * ConnectorSelectionModal
 * Modal to select a connector for executing operations (delete user, assign role, etc.)
 * 
 * Filters connectors by capability and allows user to select which connector to use.
 */
import React, { useState, useEffect } from 'react';
import { Modal, List, Button, message, Spin, Empty, Tag } from 'antd';
import { ApiOutlined, CheckCircleOutlined } from '@ant-design/icons';
import api from '../api/request';

const ConnectorSelectionModal = ({
    visible,
    onClose,
    onSelect,
    tenantId,
    capability,
    operationTitle
}) => {
    const [connectors, setConnectors] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedConnector, setSelectedConnector] = useState(null);

    useEffect(() => {
        if (visible && tenantId && capability) {
            fetchConnectorsByCapability();
        }
    }, [visible, tenantId, capability]);

    const fetchConnectorsByCapability = async () => {
        setLoading(true);
        try {
            const response = await api.get(`/tenants/${tenantId}/connectors/by-capability/${capability}`);
            setConnectors(response.connectors || []);
            if (response.connectors.length === 0) {
                message.warning(`No connectors found with '${capability}' capability`);
            }
        } catch (error) {
            console.error('Failed to fetch connectors:', error);
            message.error('Failed to load connectors');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectConnector = (connector) => {
        setSelectedConnector(connector);
        onSelect(connector);
        onClose();
    };

    const getCategoryColor = (category) => {
        const colors = {
            'SSO': 'blue',
            'APPLICATION': 'green',
            'DIRECTORY': 'purple',
            'CLOUD': 'orange'
        };
        return colors[category] || 'default';
    };

    return (
        <Modal
            title={`Select Connector for ${operationTitle}`}
            open={visible}
            on Cancel={onClose}
            footer={null}
            width={600}
        >
            <div style={{ marginBottom: 16 }}>
                <p>
                    Select a connector to execute this operation. Only connectors with the{' '}
                    <Tag color="blue">{capability}</Tag> capability are shown.
                </p>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                </div>
            ) : connectors.length === 0 ? (
                <Empty
                    description={
                        <span>
                            No connectors available for this operation.
                            <br />
                            Configure a connector with <Tag color="blue">{capability}</Tag> capability first.
                        </span>
                    }
                />
            ) : (
                <List
                    dataSource={connectors}
                    renderItem={(connector) => (
                        <List.Item
                            key={connector.id}
                            style={{
                                cursor: 'pointer',
                                borderRadius: 8,
                                marginBottom: 8,
                                padding: 16,
                                border: selectedConnector?.id === connector.id ? '2px solid #1890ff' : '1px solid #d9d9d9',
                                backgroundColor: selectedConnector?.id === connector.id ? '#e6f7ff' : 'white'
                            }}
                            onClick={() => setSelectedConnector(connector)}
                        >
                            <List.Item.Meta
                                avatar={
                                    <ApiOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                                }
                                title={
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span>{connector.name}</span>
                                        <Tag color={getCategoryColor(connector.category)}>
                                            {connector.category}
                                        </Tag>
                                        {connector.status === 'active' && (
                                            <Tag color="green" icon={<CheckCircleOutlined />}>
                                                Active
                                            </Tag>
                                        )}
                                    </div>
                                }
                                description={
                                    <div style={{ marginTop: 4 }}>
                                        <div><strong>Template:</strong> {connector.template_slug}</div>
                                        <div>
                                            <strong>Capabilities:</strong>{' '}
                                            {connector.capabilities.slice(0, 3).map(cap => (
                                                <Tag key={cap} size="small" style={{ margin: '2px' }}>
                                                    {cap}
                                                </Tag>
                                            ))}
                                            {connector.capabilities.length > 3 && (
                                                <Tag size="small">+{connector.capabilities.length - 3} more</Tag>
                                            )}
                                        </div>
                                    </div>
                                }
                            />
                            <Button
                                type={selectedConnector?.id === connector.id ? 'primary' : 'default'}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleSelectConnector(connector);
                                }}
                            >
                                {selectedConnector?.id === connector.id ? 'Selected' : 'Select'}
                            </Button>
                        </List.Item>
                    )}
                />
            )}

            <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Button onClick={onClose}>
                    Cancel
                </Button>
            </div>
        </Modal>
    );
};

export default ConnectorSelectionModal;
