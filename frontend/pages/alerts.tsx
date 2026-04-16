import React, { useState } from 'react';
import AlertManager from '../components/AlertManager';
import ShopifyIntegration from '../components/ShopifyIntegration';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const AlertsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'shopify'>('alerts');

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <button
              onClick={() => window.history.back()}
              className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span className="text-sm font-medium">Back</span>
            </button>
            <div className="h-6 w-px bg-gray-600"></div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">System Management</h1>
          <p className="text-gray-400">Monitor alerts and manage Shopify integration</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700 mb-8">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('alerts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'alerts'
                  ? 'border-yellow-500 text-yellow-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              Alert Management
            </button>
            <button
              onClick={() => setActiveTab('shopify')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'shopify'
                  ? 'border-yellow-500 text-yellow-500'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              Shopify Integration
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'alerts' && <AlertManager />}
        {activeTab === 'shopify' && <ShopifyIntegration />}
      </div>
    </div>
  );
};

export default AlertsPage;


