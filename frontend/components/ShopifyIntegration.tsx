import React, { useState, useEffect } from 'react';
import {
  ShoppingBagIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CogIcon,
  PlayIcon,
  StopIcon,
  EyeIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

interface ShopifyIntegration {
  id: number;
  shop_domain: string;
  access_token: string;
  webhook_secret?: string;
  sync_products: boolean;
  sync_inventory: boolean;
  sync_orders: boolean;
  sync_pricing: boolean;
  sync_frequency: string;
  active: boolean;
  last_sync?: string;
  last_error?: string;
  error_count: number;
  created_at: string;
  created_by: string;
  updated_at: string;
}

interface ShopifySyncLog {
  id: number;
  integration_id: number;
  sync_type: string;
  sync_direction: string;
  items_processed: number;
  items_successful: number;
  items_failed: number;
  error_message?: string;
  error_details?: any;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  status: string;
}

interface ShopifyProduct {
  id: number;
  coin_id: number;
  shopify_product_id: string;
  shopify_variant_id?: string;
  shopify_handle?: string;
  sync_status: string;
  last_synced?: string;
  sync_error?: string;
  shopify_title?: string;
  shopify_description?: string;
  shopify_price?: number;
  shopify_inventory_quantity?: number;
  created_at: string;
  updated_at: string;
}

interface ShopifyOrder {
  id: number;
  shopify_order_id: string;
  order_number?: string;
  customer_email?: string;
  customer_name?: string;
  total_price: number;
  currency: string;
  order_status?: string;
  fulfillment_status?: string;
  sync_status: string;
  last_synced?: string;
  sync_error?: string;
  order_date?: string;
  created_at: string;
  updated_at: string;
}

interface SyncStats {
  total_syncs: number;
  successful_syncs: number;
  failed_syncs: number;
  success_rate: number;
  recent_syncs: number;
}

const ShopifyIntegration: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'orders' | 'sync' | 'settings'>('overview');
  const [integration, setIntegration] = useState<ShopifyIntegration | null>(null);
  const [syncLogs, setSyncLogs] = useState<ShopifySyncLog[]>([]);
  const [products, setProducts] = useState<ShopifyProduct[]>([]);
  const [orders, setOrders] = useState<ShopifyOrder[]>([]);
  const [syncStats, setSyncStats] = useState<SyncStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateIntegration, setShowCreateIntegration] = useState(false);
  const [syncing, setSyncing] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load integration
      const integrationResponse = await fetch('/api/v1/shopify/integrations');
      if (integrationResponse.ok) {
        const integrations = await integrationResponse.json();
        if (integrations.length > 0) {
          setIntegration(integrations[0]);
          await loadIntegrationData(integrations[0].id);
        }
      }
    } catch (err) {
      setError('Failed to load Shopify integration data');
      console.error('Error loading Shopify data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrationData = async (integrationId: number) => {
    try {
      const [logsResponse, productsResponse, ordersResponse, statsResponse] = await Promise.all([
        fetch(`/api/v1/shopify/sync-logs/${integrationId}`),
        fetch(`/api/v1/shopify/products/${integrationId}`),
        fetch(`/api/v1/shopify/orders/${integrationId}`),
        fetch(`/api/v1/shopify/statistics/${integrationId}`)
      ]);

      if (logsResponse.ok) {
        const logs = await logsResponse.json();
        setSyncLogs(logs);
      }

      if (productsResponse.ok) {
        const productsData = await productsResponse.json();
        setProducts(productsData);
      }

      if (ordersResponse.ok) {
        const ordersData = await ordersResponse.json();
        setOrders(ordersData);
      }

      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setSyncStats(stats);
      }
    } catch (err) {
      console.error('Error loading integration data:', err);
    }
  };

  const testConnection = async () => {
    if (!integration) return;
    
    try {
      const response = await fetch(`/api/v1/shopify/integrations/${integration.id}/test`);
      const result = await response.json();
      
      if (result.status === 'success') {
        alert('Connection successful!');
      } else {
        alert(`Connection failed: ${result.message}`);
      }
    } catch (err) {
      alert('Error testing connection');
      console.error('Error testing connection:', err);
    }
  };

  const syncProducts = async () => {
    if (!integration) return;
    
    try {
      setSyncing('products');
      const response = await fetch('/api/v1/shopify/sync/products', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ force_sync: false })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`Products synced successfully! Processed: ${result.processed}, Successful: ${result.successful}, Failed: ${result.failed}`);
        await loadIntegrationData(integration.id);
      } else {
        alert(`Sync failed: ${result.message}`);
      }
    } catch (err) {
      alert('Error syncing products');
      console.error('Error syncing products:', err);
    } finally {
      setSyncing(null);
    }
  };

  const syncOrders = async () => {
    if (!integration) return;
    
    try {
      setSyncing('orders');
      const response = await fetch('/api/v1/shopify/sync/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ hours_back: 24 })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`Orders synced successfully! Processed: ${result.processed}, Successful: ${result.successful}, Failed: ${result.failed}`);
        await loadIntegrationData(integration.id);
      } else {
        alert(`Sync failed: ${result.message}`);
      }
    } catch (err) {
      alert('Error syncing orders');
      console.error('Error syncing orders:', err);
    } finally {
      setSyncing(null);
    }
  };

  const syncInventory = async () => {
    if (!integration) return;
    
    try {
      setSyncing('inventory');
      const response = await fetch('/api/v1/shopify/sync/inventory', {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`Inventory synced successfully! Processed: ${result.processed}, Successful: ${result.successful}, Failed: ${result.failed}`);
        await loadIntegrationData(integration.id);
      } else {
        alert(`Sync failed: ${result.message}`);
      }
    } catch (err) {
      alert('Error syncing inventory');
      console.error('Error syncing inventory:', err);
    } finally {
      setSyncing(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'completed_with_errors': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case 'synced': return 'text-green-600 bg-green-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    );
  }

  if (!integration) {
    return (
      <div className="text-center py-12">
        <ShoppingBagIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-300">No Shopify Integration</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by creating a Shopify integration.</p>
        <div className="mt-6">
          <button
            onClick={() => setShowCreateIntegration(true)}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors mx-auto"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create Integration</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Shopify Integration</h1>
          <p className="text-gray-400 mt-2">Manage your Shopify store integration and synchronization</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={testConnection}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <CheckCircleIcon className="h-5 w-5" />
            <span>Test Connection</span>
          </button>
          <button
            onClick={() => setShowCreateIntegration(true)}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <PencilIcon className="h-5 w-5" />
            <span>Edit Settings</span>
          </button>
        </div>
      </div>

      {/* Integration Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-lg ${integration.active ? 'bg-green-100' : 'bg-red-100'}`}>
              <ShoppingBagIcon className={`h-8 w-8 ${integration.active ? 'text-green-600' : 'text-red-600'}`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{integration.shop_domain}</h3>
              <p className="text-gray-400">
                {integration.active ? 'Active' : 'Inactive'} • 
                Last sync: {integration.last_sync ? formatDate(integration.last_sync) : 'Never'}
              </p>
              {integration.last_error && (
                <p className="text-red-400 text-sm mt-1">Error: {integration.last_error}</p>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-400">Error Count</p>
            <p className="text-2xl font-bold text-white">{integration.error_count}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: EyeIcon },
            { id: 'products', label: 'Products', icon: ShoppingBagIcon },
            { id: 'orders', label: 'Orders', icon: ShoppingBagIcon },
            { id: 'sync', label: 'Sync Logs', icon: ArrowPathIcon },
            { id: 'settings', label: 'Settings', icon: CogIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-yellow-500 text-yellow-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <ArrowPathIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Total Syncs</p>
                  <p className="text-2xl font-bold text-white">{syncStats?.total_syncs || 0}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Success Rate</p>
                  <p className="text-2xl font-bold text-white">{syncStats?.success_rate?.toFixed(1) || 0}%</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <ShoppingBagIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Products</p>
                  <p className="text-2xl font-bold text-white">{products.length}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <ShoppingBagIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-400">Orders</p>
                  <p className="text-2xl font-bold text-white">{orders.length}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={syncProducts}
                disabled={syncing === 'products'}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                {syncing === 'products' ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <ArrowPathIcon className="h-5 w-5" />
                )}
                <span>Sync Products</span>
              </button>
              
              <button
                onClick={syncOrders}
                disabled={syncing === 'orders'}
                className="bg-green-500 hover:bg-green-600 disabled:bg-gray-600 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                {syncing === 'orders' ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <ArrowPathIcon className="h-5 w-5" />
                )}
                <span>Sync Orders</span>
              </button>
              
              <button
                onClick={syncInventory}
                disabled={syncing === 'inventory'}
                className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
              >
                {syncing === 'inventory' ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <ArrowPathIcon className="h-5 w-5" />
                )}
                <span>Sync Inventory</span>
              </button>
            </div>
          </div>

          {/* Recent Sync Logs */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Sync Activity</h3>
            <div className="space-y-3">
              {syncLogs.slice(0, 5).map((log) => (
                <div key={log.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                      {log.status}
                    </span>
                    <div>
                      <p className="text-white font-medium">{log.sync_type} - {log.sync_direction}</p>
                      <p className="text-gray-400 text-sm">
                        {log.items_successful}/{log.items_processed} successful
                        {log.duration_seconds && ` • ${formatDuration(log.duration_seconds)}`}
                      </p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">{formatDate(log.started_at)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Products Tab */}
      {activeTab === 'products' && (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Shopify Products</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Shopify ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Inventory</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Last Synced</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {products.map((product) => (
                  <tr key={product.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">{product.shopify_title || 'N/A'}</div>
                        <div className="text-sm text-gray-400">Coin ID: {product.coin_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {product.shopify_product_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSyncStatusColor(product.sync_status)}`}>
                        {product.sync_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${product.shopify_price?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {product.shopify_inventory_quantity || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {product.last_synced ? formatDate(product.last_synced) : 'Never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Shopify Orders</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Order</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Total</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Order Date</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">#{order.order_number || order.shopify_order_id}</div>
                        <div className="text-sm text-gray-400">ID: {order.shopify_order_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">{order.customer_name || 'N/A'}</div>
                        <div className="text-sm text-gray-400">{order.customer_email || 'N/A'}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${order.total_price.toFixed(2)} {order.currency}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        order.order_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {order.order_status || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {order.order_date ? formatDate(order.order_date) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sync Logs Tab */}
      {activeTab === 'sync' && (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Sync Logs</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Direction</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Results</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Duration</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Started</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {syncLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                      {log.sync_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {log.sync_direction}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {log.items_successful}/{log.items_processed}
                      {log.items_failed > 0 && (
                        <span className="text-red-400 ml-1">({log.items_failed} failed)</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {log.duration_seconds ? formatDuration(log.duration_seconds) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatDate(log.started_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default ShopifyIntegration;


