# MC-INV-003: Bulk Operations System Implementation

## Overview
Implement comprehensive bulk operations system that maintains individual coin tracking while enabling efficient bulk processing for inventory management.

## Requirements Analysis

### Current State
- Individual coin tracking is already implemented
- Each coin has its own bought price and profit margin
- Bulk operations need to preserve individual tracking

### Key Considerations

#### 1. **Individual Coin Tracking in Bulk Operations**
- **Scenario**: 100 Mercury dimes purchased for $200 total
- **Implementation**: Create 100 individual coin records, each with $2.00 bought price
- **Benefit**: Maintains accurate profit margins and individual tracking
- **Challenge**: Efficient bulk creation and management

#### 2. **Bulk Operation Types**
- **Bulk Purchase**: Add multiple coins with same properties
- **Bulk Transfer**: Move multiple coins between locations
- **Bulk Price Update**: Update pricing for multiple coins
- **Bulk Status Change**: Change status for multiple coins
- **Bulk Collection Assignment**: Assign multiple coins to collections

#### 3. **Performance Considerations**
- **Database Transactions**: Use batch operations for efficiency
- **Progress Tracking**: Show progress for large bulk operations
- **Error Handling**: Handle partial failures gracefully
- **Rollback Capability**: Ability to undo bulk operations

## Technical Implementation

### Database Schema Updates

#### 1. **Bulk Operation Tracking**
```sql
CREATE TABLE bulk_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL, -- 'purchase', 'transfer', 'price_update', 'status_change'
    description TEXT,
    total_items INTEGER NOT NULL,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB -- Store operation-specific data
);

CREATE TABLE bulk_operation_items (
    id SERIAL PRIMARY KEY,
    bulk_operation_id INTEGER REFERENCES bulk_operations(id) ON DELETE CASCADE,
    coin_id INTEGER REFERENCES coins(id),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT,
    processed_at TIMESTAMP,
    metadata JSONB -- Store item-specific data
);
```

#### 2. **Enhanced Coin Tracking**
```sql
-- Add bulk operation reference to coins
ALTER TABLE coins ADD COLUMN bulk_operation_id INTEGER REFERENCES bulk_operations(id);
ALTER TABLE coins ADD COLUMN bulk_item_id INTEGER REFERENCES bulk_operation_items(id);

-- Add serial number tracking for bulk operations
ALTER TABLE coins ADD COLUMN serial_number VARCHAR(50);
ALTER TABLE coins ADD COLUMN bulk_sequence_number INTEGER;
```

### Backend Implementation

#### 1. **Bulk Operations Service**
```python
# backend/app/services/bulk_operations_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
from ..models import Coin, BulkOperation, BulkOperationItem
from ..schemas.bulk_operations import BulkOperationCreate, BulkOperationResponse

class BulkOperationsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_bulk_purchase(
        self, 
        operation_data: BulkOperationCreate,
        coin_data: List[Dict[str, Any]]
    ) -> BulkOperationResponse:
        """Create bulk purchase operation with individual coin tracking"""
        
        # Create bulk operation record
        bulk_op = BulkOperation(
            operation_type='purchase',
            description=operation_data.description,
            total_items=len(coin_data),
            created_by=operation_data.created_by,
            metadata=operation_data.metadata
        )
        self.db.add(bulk_op)
        self.db.flush()
        
        # Create individual coins
        coins = []
        for i, coin_info in enumerate(coin_data):
            coin = Coin(
                sku=coin_info['sku'],
                name=coin_info['name'],
                year=coin_info['year'],
                bought_price=coin_info['bought_price'],
                collection_id=coin_info.get('collection_id'),
                bulk_operation_id=bulk_op.id,
                bulk_sequence_number=i + 1,
                serial_number=f"{coin_info['sku']}-{i+1:04d}",
                status='inventory'
            )
            coins.append(coin)
            self.db.add(coin)
        
        # Create bulk operation items
        for coin in coins:
            bulk_item = BulkOperationItem(
                bulk_operation_id=bulk_op.id,
                coin_id=coin.id,
                status='pending'
            )
            self.db.add(bulk_item)
        
        self.db.commit()
        return BulkOperationResponse.from_orm(bulk_op)
    
    async def process_bulk_operation(self, operation_id: int) -> Dict[str, Any]:
        """Process bulk operation with progress tracking"""
        bulk_op = self.db.query(BulkOperation).filter(
            BulkOperation.id == operation_id
        ).first()
        
        if not bulk_op:
            raise ValueError("Bulk operation not found")
        
        bulk_op.status = 'processing'
        self.db.commit()
        
        # Process items in batches
        batch_size = 100
        processed = 0
        failed = 0
        
        while processed + failed < bulk_op.total_items:
            items = self.db.query(BulkOperationItem).filter(
                BulkOperationItem.bulk_operation_id == operation_id,
                BulkOperationItem.status == 'pending'
            ).limit(batch_size).all()
            
            if not items:
                break
            
            for item in items:
                try:
                    await self._process_item(item)
                    item.status = 'completed'
                    processed += 1
                except Exception as e:
                    item.status = 'failed'
                    item.error_message = str(e)
                    failed += 1
            
            # Update progress
            bulk_op.processed_items = processed
            bulk_op.failed_items = failed
            self.db.commit()
        
        # Complete operation
        bulk_op.status = 'completed' if failed == 0 else 'failed'
        bulk_op.completed_at = datetime.utcnow()
        self.db.commit()
        
        return {
            'operation_id': operation_id,
            'status': bulk_op.status,
            'processed': processed,
            'failed': failed
        }
    
    async def _process_item(self, item: BulkOperationItem):
        """Process individual bulk operation item"""
        # Implementation depends on operation type
        pass
```

#### 2. **Bulk Operations Router**
```python
# backend/app/routers/bulk_operations.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.bulk_operations_service import BulkOperationsService
from ..schemas.bulk_operations import (
    BulkOperationCreate, 
    BulkOperationResponse,
    BulkPurchaseRequest,
    BulkTransferRequest,
    BulkPriceUpdateRequest
)

router = APIRouter(prefix="/api/bulk-operations", tags=["bulk-operations"])

@router.post("/purchase", response_model=BulkOperationResponse)
async def create_bulk_purchase(
    request: BulkPurchaseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create bulk purchase operation"""
    service = BulkOperationsService(db)
    
    # Validate request
    if len(request.coins) > 1000:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 1000 coins per bulk operation"
        )
    
    # Create operation
    operation = await service.create_bulk_purchase(
        request.operation, 
        request.coins
    )
    
    # Process in background
    background_tasks.add_task(
        service.process_bulk_operation, 
        operation.id
    )
    
    return operation

@router.get("/{operation_id}/status")
async def get_operation_status(
    operation_id: int,
    db: Session = Depends(get_db)
):
    """Get bulk operation status and progress"""
    service = BulkOperationsService(db)
    return await service.get_operation_status(operation_id)

@router.post("/{operation_id}/cancel")
async def cancel_operation(
    operation_id: int,
    db: Session = Depends(get_db)
):
    """Cancel bulk operation"""
    service = BulkOperationsService(db)
    return await service.cancel_operation(operation_id)
```

### Frontend Implementation

#### 1. **Bulk Operations Component**
```typescript
// frontend/components/BulkOperations.tsx
import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { BulkOperationsService } from '../lib/api';

interface BulkPurchaseForm {
  description: string;
  coins: Array<{
    sku: string;
    name: string;
    year: number;
    bought_price: number;
    collection_id?: number;
  }>;
}

export const BulkOperations: React.FC = () => {
  const [formData, setFormData] = useState<BulkPurchaseForm>({
    description: '',
    coins: []
  });
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [operationId, setOperationId] = useState<number | null>(null);
  
  const createBulkPurchase = useMutation({
    mutationFn: BulkOperationsService.createBulkPurchase,
    onSuccess: (data) => {
      setOperationId(data.id);
      setIsProcessing(true);
    }
  });
  
  const { data: operationStatus } = useQuery({
    queryKey: ['bulk-operation-status', operationId],
    queryFn: () => BulkOperationsService.getOperationStatus(operationId!),
    enabled: !!operationId && isProcessing,
    refetchInterval: 2000 // Poll every 2 seconds
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createBulkPurchase.mutateAsync(formData);
  };
  
  const addCoin = () => {
    setFormData(prev => ({
      ...prev,
      coins: [...prev.coins, {
        sku: '',
        name: '',
        year: new Date().getFullYear(),
        bought_price: 0
      }]
    }));
  };
  
  const removeCoin = (index: number) => {
    setFormData(prev => ({
      ...prev,
      coins: prev.coins.filter((_, i) => i !== index)
    }));
  };
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Bulk Operations</h1>
      
      {isProcessing && operationStatus && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-2">Processing Operation</h3>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ 
                width: `${(operationStatus.processed / operationStatus.total) * 100}%` 
              }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {operationStatus.processed} of {operationStatus.total} items processed
          </p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            Operation Description
          </label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              description: e.target.value 
            }))}
            className="w-full p-3 border rounded-lg"
            placeholder="e.g., Bulk purchase of 100 Mercury dimes"
            required
          />
        </div>
        
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Coins</h3>
            <button
              type="button"
              onClick={addCoin}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Coin
            </button>
          </div>
          
          <div className="space-y-4">
            {formData.coins.map((coin, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">SKU</label>
                    <input
                      type="text"
                      value={coin.sku}
                      onChange={(e) => {
                        const newCoins = [...formData.coins];
                        newCoins[index].sku = e.target.value;
                        setFormData(prev => ({ ...prev, coins: newCoins }));
                      }}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={coin.name}
                      onChange={(e) => {
                        const newCoins = [...formData.coins];
                        newCoins[index].name = e.target.value;
                        setFormData(prev => ({ ...prev, coins: newCoins }));
                      }}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Year</label>
                    <input
                      type="number"
                      value={coin.year}
                      onChange={(e) => {
                        const newCoins = [...formData.coins];
                        newCoins[index].year = parseInt(e.target.value);
                        setFormData(prev => ({ ...prev, coins: newCoins }));
                      }}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Bought Price</label>
                    <input
                      type="number"
                      step="0.01"
                      value={coin.bought_price}
                      onChange={(e) => {
                        const newCoins = [...formData.coins];
                        newCoins[index].bought_price = parseFloat(e.target.value);
                        setFormData(prev => ({ ...prev, coins: newCoins }));
                      }}
                      className="w-full p-2 border rounded"
                      required
                    />
                  </div>
                </div>
                
                <button
                  type="button"
                  onClick={() => removeCoin(index)}
                  className="mt-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
        
        <button
          type="submit"
          disabled={createBulkPurchase.isPending || formData.coins.length === 0}
          className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {createBulkPurchase.isPending ? 'Creating...' : 'Create Bulk Purchase'}
        </button>
      </form>
    </div>
  );
};
```

## Implementation Plan

### Phase 1: Core Bulk Operations (Week 1)
- [ ] Create database schema for bulk operations
- [ ] Implement bulk operations service
- [ ] Create API endpoints for bulk operations
- [ ] Implement basic bulk purchase functionality

### Phase 2: Enhanced Features (Week 2)
- [ ] Add bulk transfer operations
- [ ] Implement bulk price updates
- [ ] Add bulk status changes
- [ ] Create progress tracking system

### Phase 3: Frontend Integration (Week 3)
- [ ] Create bulk operations UI components
- [ ] Implement real-time progress tracking
- [ ] Add bulk operation history
- [ ] Create bulk operation management dashboard

### Phase 4: Advanced Features (Week 4)
- [ ] Add bulk operation templates
- [ ] Implement bulk operation scheduling
- [ ] Add bulk operation analytics
- [ ] Create bulk operation reports

## Success Criteria
- [ ] Can create 100+ individual coins in single operation
- [ ] Maintains individual profit margins and tracking
- [ ] Real-time progress tracking for bulk operations
- [ ] Error handling and rollback capabilities
- [ ] Performance optimized for large operations
- [ ] User-friendly interface for bulk operations

## Questions for Owner

1. **Bulk Operation Limits**: What's the maximum number of coins per bulk operation? (Suggested: 1000)

2. **Serial Number Format**: What format should we use for serial numbers? (Suggested: SKU-0001, SKU-0002, etc.)

3. **Bulk Operation Types**: Which bulk operations are most important? (Purchase, Transfer, Price Update, Status Change)

4. **Progress Tracking**: How detailed should progress tracking be? (Per coin, per batch, overall)

5. **Error Handling**: How should we handle partial failures? (Continue processing, stop on first error, retry failed items)

6. **Bulk Templates**: Should we support saving bulk operation templates for common operations?

7. **Bulk Scheduling**: Should bulk operations be schedulable for off-peak hours?

8. **Bulk Analytics**: What analytics should we provide for bulk operations? (Success rates, processing times, error patterns)

## Next Steps
1. Review and approve the bulk operations design
2. Implement Phase 1 core functionality
3. Test with sample data
4. Iterate based on feedback
5. Implement remaining phases

---

**Priority**: High
**Estimated Time**: 4 weeks
**Dependencies**: None
**Status**: Ready for implementation
