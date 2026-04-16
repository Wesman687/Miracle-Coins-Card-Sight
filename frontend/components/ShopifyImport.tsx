import React, { useState, useEffect } from 'react';
import { 
  CloudArrowDownIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  TagIcon,
  DocumentTextIcon,
  CubeIcon
} from '@heroicons/react/24/outline';

interface ShopifyCollection {
  id: number;
  title: string;
  handle: string;
  description: string;
  product_count: number;
  created_at: string;
  updated_at: string;
  metafields: Array<{
    id: number;
    namespace: string;
    key: string;
    value: string;
    type: string;
    description?: string;
  }>;
  product_types: string[];
  image?: {
    src: string;
    alt: string;
  };
  rules: Array<{
    column: string;
    relation: string;
    condition: string;
  }>;
}

interface ShopifyIntegration {
  id: number;
  shop_domain: string;
  active: boolean;
  sync_products: boolean;
  sync_inventory: boolean;
  sync_orders: boolean;
}

interface ImportResult {
  status: string;
  imported_categories: number;
  updated_categories: number;
  total_processed: number;
  errors: string[];
}

const ShopifyImport: React.FC = () => {
  const [integrations, setIntegrations] = useState<ShopifyIntegration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<number | null>(null);
  const [collections, setCollections] = useState<ShopifyCollection[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<number | null>(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      // This would fetch from your integrations endpoint
      // For now, we'll use a mock integration
      setIntegrations([{
        id: 1,
        shop_domain: 'miracle-coins.myshopify.com',
        active: true,
        sync_products: true,
        sync_inventory: true,
        sync_orders: true
      }]);
      setSelectedIntegration(1);
    } catch (err) {
      setError('Failed to fetch Shopify integrations');
    }
  };

  const fetchCollections = async () => {
    if (!selectedIntegration) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/v1/categories/shopify/fetch?integration_id=${selectedIntegration}`);
      if (!response.ok) {
        throw new Error('Failed to fetch collections');
      }

      const data = await response.json();
      setCollections(data.collections || []);
      
      // Auto-select all collections
      setSelectedCollections(data.collections?.map((c: ShopifyCollection) => c.id) || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch collections');
    } finally {
      setLoading(false);
    }
  };

  const importCollections = async () => {
    if (!selectedIntegration || selectedCollections.length === 0) return;

    try {
      setImporting(true);
      setError(null);
      
      const response = await fetch('/api/v1/categories/shopify/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          integration_id: selectedIntegration,
          collection_ids: selectedCollections
        })
      });

      if (!response.ok) {
        throw new Error('Failed to import collections');
      }

      const result = await response.json();
      setImportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import collections');
    } finally {
      setImporting(false);
    }
  };

  const toggleCollectionSelection = (collectionId: number) => {
    setSelectedCollections(prev => 
      prev.includes(collectionId)
        ? prev.filter(id => id !== collectionId)
        : [...prev, collectionId]
    );
  };

  const selectAllCollections = () => {
    setSelectedCollections(collections.map(c => c.id));
  };

  const deselectAllCollections = () => {
    setSelectedCollections([]);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Import Shopify Collections</h2>
          <p className="text-gray-600">Import your existing Shopify collections as coin categories</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <InformationCircleIcon className="h-5 w-5" />
          <span>This will preserve all metadata and product types</span>
        </div>
      </div>

      {/* Integration Selection */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Shopify Integration</h3>
        <div className="space-y-3">
          {integrations.map((integration) => (
            <label key={integration.id} className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                name="integration"
                value={integration.id}
                checked={selectedIntegration === integration.id}
                onChange={(e) => setSelectedIntegration(Number(e.target.value))}
                className="h-4 w-4 text-gold-600 focus:ring-gold-500 border-gray-300"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{integration.shop_domain}</div>
                <div className="text-sm text-gray-500">
                  Products: {integration.sync_products ? 'Enabled' : 'Disabled'} • 
                  Inventory: {integration.sync_inventory ? 'Enabled' : 'Disabled'} • 
                  Orders: {integration.sync_orders ? 'Enabled' : 'Disabled'}
                </div>
              </div>
              <span className={`px-2 py-1 text-xs rounded-full ${
                integration.active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {integration.active ? 'Active' : 'Inactive'}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Fetch Collections Button */}
      {selectedIntegration && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Fetch Collections</h3>
              <p className="text-gray-600">Retrieve all collections and their metadata from Shopify</p>
            </div>
            <button
              onClick={fetchCollections}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Fetching...
                </>
              ) : (
                <>
                  <CloudArrowDownIcon className="h-5 w-5" />
                  Fetch Collections
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Collections List */}
      {collections.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Select Collections to Import ({selectedCollections.length}/{collections.length})
                </h3>
                <p className="text-gray-600">Choose which collections to import as coin categories</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={selectAllCollections}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Select All
                </button>
                <button
                  onClick={deselectAllCollections}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Deselect All
                </button>
              </div>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {collections.map((collection) => (
              <div key={collection.id} className="p-6">
                <div className="flex items-start space-x-4">
                  <input
                    type="checkbox"
                    checked={selectedCollections.includes(collection.id)}
                    onChange={() => toggleCollectionSelection(collection.id)}
                    className="mt-1 h-4 w-4 text-gold-600 focus:ring-gold-500 border-gray-300 rounded"
                  />
                  
                  {/* Collection Image */}
                  {collection.image && (
                    <div className="flex-shrink-0">
                      <img
                        src={collection.image.src}
                        alt={collection.image.alt}
                        className="h-16 w-16 rounded-lg object-cover"
                      />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-medium text-gray-900 truncate">
                        {collection.title}
                      </h4>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span>{collection.product_count} products</span>
                        <span>•</span>
                        <span>Updated {formatDate(collection.updated_at)}</span>
                      </div>
                    </div>

                    {collection.description && (
                      <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                        {collection.description}
                      </p>
                    )}

                    {/* Metadata Summary */}
                    <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
                      {collection.metafields.length > 0 && (
                        <div className="flex items-center gap-1">
                          <DocumentTextIcon className="h-4 w-4" />
                          <span>{collection.metafields.length} metafields</span>
                        </div>
                      )}
                      {collection.product_types.length > 0 && (
                        <div className="flex items-center gap-1">
                          <CubeIcon className="h-4 w-4" />
                          <span>{collection.product_types.length} product types</span>
                        </div>
                      )}
                      {collection.rules.length > 0 && (
                        <div className="flex items-center gap-1">
                          <TagIcon className="h-4 w-4" />
                          <span>{collection.rules.length} rules</span>
                        </div>
                      )}
                    </div>

                    {/* Show Details Button */}
                    <button
                      onClick={() => setShowDetails(showDetails === collection.id ? null : collection.id)}
                      className="mt-2 text-sm text-gold-600 hover:text-gold-700"
                    >
                      {showDetails === collection.id ? 'Hide Details' : 'Show Details'}
                    </button>

                    {/* Detailed Information */}
                    {showDetails === collection.id && (
                      <div className="mt-4 space-y-4">
                        {/* Metafields */}
                        {collection.metafields.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-900 mb-2">Metafields</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {collection.metafields.map((metafield) => (
                                <div key={metafield.id} className="bg-gray-50 p-3 rounded-lg">
                                  <div className="text-sm font-medium text-gray-900">
                                    {metafield.namespace}.{metafield.key}
                                  </div>
                                  <div className="text-sm text-gray-600">{metafield.value}</div>
                                  <div className="text-xs text-gray-500">{metafield.type}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Product Types */}
                        {collection.product_types.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-900 mb-2">Product Types</h5>
                            <div className="flex flex-wrap gap-2">
                              {collection.product_types.map((type, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                                >
                                  {type}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Rules */}
                        {collection.rules.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-900 mb-2">Collection Rules</h5>
                            <div className="space-y-2">
                              {collection.rules.map((rule, index) => (
                                <div key={index} className="bg-gray-50 p-3 rounded-lg">
                                  <div className="text-sm text-gray-900">
                                    {rule.column} {rule.relation} {rule.condition}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Import Button */}
      {selectedCollections.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Import Selected Collections</h3>
              <p className="text-gray-600">
                Import {selectedCollections.length} collection{selectedCollections.length !== 1 ? 's' : ''} as coin categories
              </p>
            </div>
            <button
              onClick={importCollections}
              disabled={importing || selectedCollections.length === 0}
              className="bg-gold-600 text-white px-6 py-3 rounded-lg hover:bg-gold-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {importing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Importing...
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-5 w-5" />
                  Import Collections
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Import Results */}
      {importResult && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Results</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{importResult.imported_categories}</div>
              <div className="text-sm text-green-700">New Categories</div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{importResult.updated_categories}</div>
              <div className="text-sm text-blue-700">Updated Categories</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">{importResult.total_processed}</div>
              <div className="text-sm text-gray-700">Total Processed</div>
            </div>
          </div>

          {importResult.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
                <h4 className="text-sm font-medium text-red-800">Errors</h4>
              </div>
              <ul className="text-sm text-red-700 space-y-1">
                {importResult.errors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <div className="text-red-800">{error}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShopifyImport;
