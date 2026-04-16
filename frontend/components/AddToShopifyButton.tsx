import React, { useState } from 'react';
import { shopifyAPI } from '../lib/api';

interface AddToShopifyButtonProps {
  coinId: number;
  coinTitle: string;
  integrationId: number;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const AddToShopifyButton: React.FC<AddToShopifyButtonProps> = ({
  coinId,
  coinTitle,
  integrationId,
  onSuccess,
  onError
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAdded, setIsAdded] = useState(false);

  const handleAddToShopify = async () => {
    setIsLoading(true);
    try {
      const response = await shopifyAPI.createProductAndInventory(coinId, integrationId);
      
      if (response.data.status === 'success') {
        setIsAdded(true);
        onSuccess?.();
        console.log(`✅ Added ${coinTitle} to Shopify and inventory:`, response.data);
      } else {
        throw new Error(response.data.message || 'Failed to add product');
      }
    } catch (error: any) {
      console.error('❌ Error adding product to Shopify:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Unknown error';
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (isAdded) {
    return (
      <button
        disabled
        className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-600 bg-green-100 rounded-full"
      >
        ✅ Added to Shopify
      </button>
    );
  }

  return (
    <button
      onClick={handleAddToShopify}
      disabled={isLoading}
      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-full transition-colors"
    >
      {isLoading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Adding...
        </>
      ) : (
        <>
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add to Shopify
        </>
      )}
    </button>
  );
};

export default AddToShopifyButton;
