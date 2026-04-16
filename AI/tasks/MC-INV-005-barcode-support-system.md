# MC-INV-005: Barcode Support Implementation

## Overview
Implement comprehensive barcode scanning and generation capabilities for inventory management, including QR codes, UPC codes, and custom barcode formats.

## Requirements Analysis

### Current State
- No barcode support in current system
- Manual SKU entry and tracking
- No mobile scanning capabilities

### Key Requirements

#### 1. **Barcode Generation**
- Generate unique barcodes for each coin
- Support multiple barcode formats (QR, UPC, Code128)
- Link barcodes to coin records
- Print barcode labels

#### 2. **Barcode Scanning**
- Mobile app integration for scanning
- Web-based scanning capabilities
- Bulk scanning for inventory operations
- Offline scanning support

#### 3. **Barcode Management**
- Barcode database and tracking
- Barcode validation and verification
- Barcode history and usage tracking
- Barcode replacement and updates

## Technical Implementation

### Database Schema Updates

#### 1. **Barcode System Tables**
```sql
-- Barcode types table
CREATE TABLE barcode_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- 'QR', 'UPC', 'Code128', 'Custom'
    format VARCHAR(20) NOT NULL, -- 'qr', 'upc', 'code128', 'custom'
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Barcodes table
CREATE TABLE barcodes (
    id SERIAL PRIMARY KEY,
    barcode_value VARCHAR(255) NOT NULL UNIQUE,
    barcode_type_id INTEGER REFERENCES barcode_types(id),
    coin_id INTEGER REFERENCES coins(id),
    generated_by INTEGER REFERENCES users(id),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    scan_count INTEGER DEFAULT 0,
    last_scanned_at TIMESTAMP,
    metadata JSONB -- Store barcode-specific data
);

-- Barcode scans table
CREATE TABLE barcode_scans (
    id SERIAL PRIMARY KEY,
    barcode_id INTEGER REFERENCES barcodes(id),
    scanned_by INTEGER REFERENCES users(id),
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_location VARCHAR(100), -- 'warehouse', 'store', 'mobile'
    scan_purpose VARCHAR(50), -- 'inventory', 'sale', 'transfer', 'audit'
    device_info JSONB, -- Store device information
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Barcode templates table
CREATE TABLE barcode_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    barcode_type_id INTEGER REFERENCES barcode_types(id),
    template_data JSONB, -- Store template configuration
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default barcode types
INSERT INTO barcode_types (name, format, description) VALUES
('QR Code', 'qr', 'QR code format for mobile scanning'),
('UPC', 'upc', 'Universal Product Code format'),
('Code128', 'code128', 'Code128 barcode format'),
('Custom', 'custom', 'Custom barcode format');
```

#### 2. **Enhanced Coin Table**
```sql
-- Add barcode reference to coins table
ALTER TABLE coins ADD COLUMN barcode_id INTEGER REFERENCES barcodes(id);
ALTER TABLE coins ADD COLUMN barcode_value VARCHAR(255);
ALTER TABLE coins ADD COLUMN barcode_generated_at TIMESTAMP;
```

### Backend Implementation

#### 1. **Barcode Service**
```python
# backend/app/services/barcode_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import qrcode
import barcode
from barcode.writer import ImageWriter
import io
import base64
from datetime import datetime
from ..models import Barcode, BarcodeType, BarcodeScan, Coin
from ..schemas.barcode import BarcodeCreate, BarcodeResponse, BarcodeScanRequest

class BarcodeService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_barcode(
        self, 
        coin_id: int, 
        barcode_type: str = 'qr',
        custom_value: Optional[str] = None
    ) -> BarcodeResponse:
        """Generate barcode for a coin"""
        
        # Get coin information
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            raise ValueError("Coin not found")
        
        # Get barcode type
        barcode_type_obj = self.db.query(BarcodeType).filter(
            BarcodeType.format == barcode_type
        ).first()
        if not barcode_type_obj:
            raise ValueError("Barcode type not found")
        
        # Generate barcode value
        if custom_value:
            barcode_value = custom_value
        else:
            barcode_value = self._generate_barcode_value(coin, barcode_type)
        
        # Check if barcode already exists
        existing_barcode = self.db.query(Barcode).filter(
            Barcode.barcode_value == barcode_value
        ).first()
        
        if existing_barcode:
            raise ValueError("Barcode already exists")
        
        # Create barcode record
        barcode_obj = Barcode(
            barcode_value=barcode_value,
            barcode_type_id=barcode_type_obj.id,
            coin_id=coin_id,
            generated_by=1,  # Current user
            metadata={
                'coin_sku': coin.sku,
                'coin_name': coin.name,
                'generated_at': datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(barcode_obj)
        self.db.flush()
        
        # Update coin with barcode reference
        coin.barcode_id = barcode_obj.id
        coin.barcode_value = barcode_value
        coin.barcode_generated_at = datetime.utcnow()
        
        self.db.commit()
        
        return BarcodeResponse.from_orm(barcode_obj)
    
    def _generate_barcode_value(self, coin: Coin, barcode_type: str) -> str:
        """Generate unique barcode value based on coin and type"""
        
        if barcode_type == 'qr':
            # QR code format: MC-{SKU}-{TIMESTAMP}
            timestamp = int(datetime.utcnow().timestamp())
            return f"MC-{coin.sku}-{timestamp}"
        
        elif barcode_type == 'upc':
            # UPC format: 12-digit number
            # Use coin ID and SKU to generate unique UPC
            coin_id_str = str(coin.id).zfill(6)
            sku_hash = hash(coin.sku) % 1000000
            return f"{coin_id_str}{sku_hash:06d}"
        
        elif barcode_type == 'code128':
            # Code128 format: MC{SKU}{ID}
            return f"MC{coin.sku}{coin.id:06d}"
        
        else:
            # Custom format
            return f"MC-{coin.sku}-{coin.id}"
    
    def generate_barcode_image(
        self, 
        barcode_value: str, 
        barcode_type: str,
        size: tuple = (200, 200)
    ) -> str:
        """Generate barcode image as base64 string"""
        
        if barcode_type == 'qr':
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(barcode_value)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize image
            img = img.resize(size)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        
        elif barcode_type == 'upc':
            # Generate UPC barcode
            upc = barcode.get_barcode_class('upc')
            upc_barcode = upc(barcode_value, writer=ImageWriter())
            
            # Save to buffer
            buffer = io.BytesIO()
            upc_barcode.write(buffer)
            buffer.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        
        elif barcode_type == 'code128':
            # Generate Code128 barcode
            code128 = barcode.get_barcode_class('code128')
            code128_barcode = code128(barcode_value, writer=ImageWriter())
            
            # Save to buffer
            buffer = io.BytesIO()
            code128_barcode.write(buffer)
            buffer.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
        
        else:
            raise ValueError("Unsupported barcode type")
    
    def scan_barcode(
        self, 
        barcode_value: str, 
        scan_request: BarcodeScanRequest
    ) -> Dict[str, Any]:
        """Process barcode scan"""
        
        # Find barcode
        barcode_obj = self.db.query(Barcode).filter(
            Barcode.barcode_value == barcode_value
        ).first()
        
        if not barcode_obj:
            return {
                'success': False,
                'error': 'Barcode not found',
                'barcode_value': barcode_value
            }
        
        # Create scan record
        scan = BarcodeScan(
            barcode_id=barcode_obj.id,
            scanned_by=scan_request.scanned_by,
            scan_location=scan_request.scan_location,
            scan_purpose=scan_request.scan_purpose,
            device_info=scan_request.device_info,
            success=True
        )
        
        self.db.add(scan)
        
        # Update barcode scan count
        barcode_obj.scan_count += 1
        barcode_obj.last_scanned_at = datetime.utcnow()
        
        self.db.commit()
        
        # Get coin information
        coin = self.db.query(Coin).filter(Coin.id == barcode_obj.coin_id).first()
        
        return {
            'success': True,
            'barcode': BarcodeResponse.from_orm(barcode_obj),
            'coin': {
                'id': coin.id,
                'sku': coin.sku,
                'name': coin.name,
                'year': coin.year,
                'bought_price': coin.bought_price,
                'status': coin.status
            },
            'scan_count': barcode_obj.scan_count
        }
    
    def bulk_generate_barcodes(
        self, 
        coin_ids: List[int], 
        barcode_type: str = 'qr'
    ) -> List[BarcodeResponse]:
        """Generate barcodes for multiple coins"""
        
        barcodes = []
        
        for coin_id in coin_ids:
            try:
                barcode = self.generate_barcode(coin_id, barcode_type)
                barcodes.append(barcode)
            except Exception as e:
                # Log error but continue with other coins
                print(f"Error generating barcode for coin {coin_id}: {e}")
        
        return barcodes
    
    def get_barcode_statistics(self) -> Dict[str, Any]:
        """Get barcode usage statistics"""
        
        stats = self.db.execute(text("""
            SELECT 
                bt.name as barcode_type,
                COUNT(b.id) as total_barcodes,
                SUM(b.scan_count) as total_scans,
                AVG(b.scan_count) as avg_scans_per_barcode,
                COUNT(CASE WHEN b.is_active = true THEN 1 END) as active_barcodes
            FROM barcode_types bt
            LEFT JOIN barcodes b ON bt.id = b.barcode_type_id
            GROUP BY bt.id, bt.name
        """)).fetchall()
        
        return {
            'barcode_types': [
                {
                    'type': stat.barcode_type,
                    'total_barcodes': stat.total_barcodes,
                    'total_scans': stat.total_scans,
                    'avg_scans_per_barcode': float(stat.avg_scans_per_barcode) if stat.avg_scans_per_barcode else 0,
                    'active_barcodes': stat.active_barcodes
                }
                for stat in stats
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
```

#### 2. **Barcode Router**
```python
# backend/app/routers/barcode.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..services.barcode_service import BarcodeService
from ..schemas.barcode import (
    BarcodeCreate, 
    BarcodeResponse, 
    BarcodeScanRequest,
    BarcodeScanResponse
)

router = APIRouter(prefix="/api/barcode", tags=["barcode"])

@router.post("/generate/{coin_id}", response_model=BarcodeResponse)
async def generate_barcode(
    coin_id: int,
    barcode_type: str = Query('qr', description="Barcode type: qr, upc, code128"),
    custom_value: Optional[str] = Query(None, description="Custom barcode value"),
    db: Session = Depends(get_db)
):
    """Generate barcode for a coin"""
    service = BarcodeService(db)
    return service.generate_barcode(coin_id, barcode_type, custom_value)

@router.post("/bulk-generate", response_model=List[BarcodeResponse])
async def bulk_generate_barcodes(
    coin_ids: List[int],
    barcode_type: str = Query('qr', description="Barcode type: qr, upc, code128"),
    db: Session = Depends(get_db)
):
    """Generate barcodes for multiple coins"""
    service = BarcodeService(db)
    return service.bulk_generate_barcodes(coin_ids, barcode_type)

@router.get("/image/{barcode_value}")
async def get_barcode_image(
    barcode_value: str,
    barcode_type: str = Query('qr', description="Barcode type: qr, upc, code128"),
    size: str = Query('200x200', description="Image size in format WIDTHxHEIGHT"),
    db: Session = Depends(get_db)
):
    """Get barcode image"""
    service = BarcodeService(db)
    
    # Parse size
    width, height = map(int, size.split('x'))
    
    try:
        image_data = service.generate_barcode_image(
            barcode_value, 
            barcode_type, 
            (width, height)
        )
        return {"image_data": image_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/scan", response_model=BarcodeScanResponse)
async def scan_barcode(
    barcode_value: str,
    scan_request: BarcodeScanRequest,
    db: Session = Depends(get_db)
):
    """Process barcode scan"""
    service = BarcodeService(db)
    return service.scan_barcode(barcode_value, scan_request)

@router.get("/statistics")
async def get_barcode_statistics(
    db: Session = Depends(get_db)
):
    """Get barcode usage statistics"""
    service = BarcodeService(db)
    return service.get_barcode_statistics()

@router.get("/types")
async def get_barcode_types(
    db: Session = Depends(get_db)
):
    """Get available barcode types"""
    service = BarcodeService(db)
    return service.get_barcode_types()
```

### Frontend Implementation

#### 1. **Barcode Scanner Component**
```typescript
// frontend/components/BarcodeScanner.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { BarcodeService } from '../lib/api';

interface BarcodeScannerProps {
  onScan: (result: any) => void;
  onError?: (error: string) => void;
}

export const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ 
  onScan, 
  onError 
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string>('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const scanBarcode = useMutation({
    mutationFn: BarcodeService.scanBarcode,
    onSuccess: (data) => {
      if (data.success) {
        onScan(data);
        setScanResult('');
      } else {
        onError?.(data.error);
      }
    },
    onError: (error) => {
      onError?.(error.message);
    }
  });
  
  const startScanning = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsScanning(true);
      }
    } catch (error) {
      onError?.('Camera access denied');
    }
  };
  
  const stopScanning = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      setIsScanning(false);
    }
  };
  
  const captureFrame = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');
      
      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        // Here you would integrate with a barcode scanning library
        // For now, we'll simulate scanning
        const barcodeValue = prompt('Enter barcode value (simulated):');
        if (barcodeValue) {
          setScanResult(barcodeValue);
          scanBarcode.mutate({
            barcode_value: barcodeValue,
            scanned_by: 1, // Current user
            scan_location: 'mobile',
            scan_purpose: 'inventory',
            device_info: {
              userAgent: navigator.userAgent,
              platform: navigator.platform
            }
          });
        }
      }
    }
  };
  
  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, []);
  
  return (
    <div className="max-w-md mx-auto p-4">
      <h2 className="text-xl font-semibold mb-4">Barcode Scanner</h2>
      
      <div className="mb-4">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="w-full h-64 bg-gray-200 rounded"
          style={{ display: isScanning ? 'block' : 'none' }}
        />
        
        <canvas
          ref={canvasRef}
          className="w-full h-64 bg-gray-200 rounded"
          style={{ display: 'none' }}
        />
        
        {!isScanning && (
          <div className="w-full h-64 bg-gray-200 rounded flex items-center justify-center">
            <p className="text-gray-500">Camera not active</p>
          </div>
        )}
      </div>
      
      <div className="flex space-x-2 mb-4">
        <button
          onClick={startScanning}
          disabled={isScanning}
          className="flex-1 py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Start Scanning
        </button>
        
        <button
          onClick={stopScanning}
          disabled={!isScanning}
          className="flex-1 py-2 px-4 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
        >
          Stop Scanning
        </button>
      </div>
      
      <button
        onClick={captureFrame}
        disabled={!isScanning}
        className="w-full py-2 px-4 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
      >
        Capture & Scan
      </button>
      
      {scanResult && (
        <div className="mt-4 p-3 bg-green-50 rounded">
          <p className="text-green-800">Scanned: {scanResult}</p>
        </div>
      )}
      
      {scanBarcode.isPending && (
        <div className="mt-4 p-3 bg-blue-50 rounded">
          <p className="text-blue-800">Processing scan...</p>
        </div>
      )}
    </div>
  );
};
```

#### 2. **Barcode Management Component**
```typescript
// frontend/components/BarcodeManager.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BarcodeService } from '../lib/api';

export const BarcodeManager: React.FC = () => {
  const [selectedCoins, setSelectedCoins] = useState<number[]>([]);
  const [barcodeType, setBarcodeType] = useState('qr');
  
  const queryClient = useQueryClient();
  
  const { data: coins } = useQuery({
    queryKey: ['coins-without-barcodes'],
    queryFn: () => BarcodeService.getCoinsWithoutBarcodes()
  });
  
  const generateBarcode = useMutation({
    mutationFn: BarcodeService.generateBarcode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coins-without-barcodes'] });
      queryClient.invalidateQueries({ queryKey: ['barcode-statistics'] });
    }
  });
  
  const bulkGenerateBarcodes = useMutation({
    mutationFn: BarcodeService.bulkGenerateBarcodes,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coins-without-barcodes'] });
      queryClient.invalidateQueries({ queryKey: ['barcode-statistics'] });
      setSelectedCoins([]);
    }
  });
  
  const { data: statistics } = useQuery({
    queryKey: ['barcode-statistics'],
    queryFn: BarcodeService.getBarcodeStatistics
  });
  
  const handleCoinSelect = (coinId: number) => {
    setSelectedCoins(prev => 
      prev.includes(coinId) 
        ? prev.filter(id => id !== coinId)
        : [...prev, coinId]
    );
  };
  
  const handleBulkGenerate = () => {
    if (selectedCoins.length > 0) {
      bulkGenerateBarcodes.mutate({
        coin_ids: selectedCoins,
        barcode_type: barcodeType
      });
    }
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Barcode Management</h1>
      
      {/* Statistics */}
      {statistics && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">Barcode Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {statistics.barcode_types.map((stat) => (
              <div key={stat.type} className="p-3 bg-white rounded border">
                <h3 className="font-semibold">{stat.type}</h3>
                <p className="text-sm text-gray-600">
                  Total: {stat.total_barcodes}
                </p>
                <p className="text-sm text-gray-600">
                  Scans: {stat.total_scans}
                </p>
                <p className="text-sm text-gray-600">
                  Active: {stat.active_barcodes}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Bulk Operations */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Bulk Barcode Generation</h2>
        
        <div className="flex items-center space-x-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Barcode Type</label>
            <select
              value={barcodeType}
              onChange={(e) => setBarcodeType(e.target.value)}
              className="p-2 border rounded"
            >
              <option value="qr">QR Code</option>
              <option value="upc">UPC</option>
              <option value="code128">Code128</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={handleBulkGenerate}
              disabled={selectedCoins.length === 0 || bulkGenerateBarcodes.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {bulkGenerateBarcodes.isPending ? 'Generating...' : `Generate ${selectedCoins.length} Barcodes`}
            </button>
          </div>
        </div>
        
        <p className="text-sm text-gray-600">
          Selected {selectedCoins.length} coins for barcode generation
        </p>
      </div>
      
      {/* Coins without barcodes */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Coins Without Barcodes</h2>
        
        {coins && coins.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border border-gray-300 p-2">
                    <input
                      type="checkbox"
                      checked={selectedCoins.length === coins.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedCoins(coins.map(coin => coin.id));
                        } else {
                          setSelectedCoins([]);
                        }
                      }}
                    />
                  </th>
                  <th className="border border-gray-300 p-2">SKU</th>
                  <th className="border border-gray-300 p-2">Name</th>
                  <th className="border border-gray-300 p-2">Year</th>
                  <th className="border border-gray-300 p-2">Status</th>
                  <th className="border border-gray-300 p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {coins.map((coin) => (
                  <tr key={coin.id}>
                    <td className="border border-gray-300 p-2">
                      <input
                        type="checkbox"
                        checked={selectedCoins.includes(coin.id)}
                        onChange={() => handleCoinSelect(coin.id)}
                      />
                    </td>
                    <td className="border border-gray-300 p-2">{coin.sku}</td>
                    <td className="border border-gray-300 p-2">{coin.name}</td>
                    <td className="border border-gray-300 p-2">{coin.year}</td>
                    <td className="border border-gray-300 p-2">{coin.status}</td>
                    <td className="border border-gray-300 p-2">
                      <button
                        onClick={() => generateBarcode.mutate({
                          coin_id: coin.id,
                          barcode_type: barcodeType
                        })}
                        disabled={generateBarcode.isPending}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        Generate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            All coins have barcodes generated
          </div>
        )}
      </div>
    </div>
  );
};
```

## Implementation Plan

### Phase 1: Core Barcode System (Week 1)
- [ ] Create barcode database schema
- [ ] Implement barcode generation service
- [ ] Create API endpoints for barcode operations
- [ ] Implement basic barcode generation

### Phase 2: Barcode Scanning (Week 2)
- [ ] Implement barcode scanning service
- [ ] Create mobile scanning capabilities
- [ ] Add bulk scanning functionality
- [ ] Implement scan tracking and analytics

### Phase 3: Frontend Integration (Week 3)
- [ ] Create barcode management UI
- [ ] Implement barcode scanner component
- [ ] Add barcode image generation
- [ ] Create barcode statistics dashboard

### Phase 4: Advanced Features (Week 4)
- [ ] Add barcode templates and customization
- [ ] Implement barcode printing capabilities
- [ ] Add barcode validation and verification
- [ ] Create barcode export and import

## Success Criteria
- [ ] Generate unique barcodes for all coins
- [ ] Support multiple barcode formats (QR, UPC, Code128)
- [ ] Mobile scanning capabilities
- [ ] Bulk barcode generation and scanning
- [ ] Barcode tracking and analytics
- [ ] Print barcode labels

## Questions for Owner

1. **Barcode Format**: Which barcode format is preferred? (QR codes are most versatile for mobile scanning)

2. **Barcode Value**: What format should barcode values use? (Suggested: MC-{SKU}-{TIMESTAMP} for QR codes)

3. **Mobile App**: Do you need a dedicated mobile app for scanning, or is web-based scanning sufficient?

4. **Barcode Printing**: Do you need barcode label printing capabilities? (Thermal printers, standard printers)

5. **Barcode Validation**: Should barcodes be validated against existing inventory? (Prevent duplicates, verify authenticity)

6. **Offline Scanning**: Do you need offline scanning capabilities for areas without internet?

7. **Barcode Analytics**: What analytics are most important? (Scan frequency, scan locations, scan purposes)

8. **Barcode Replacement**: Should users be able to regenerate barcodes if needed?

## Next Steps
1. Review and approve the barcode system design
2. Implement Phase 1 core functionality
3. Test with sample data
4. Iterate based on feedback
5. Implement remaining phases

---

**Priority**: High
**Estimated Time**: 4 weeks
**Dependencies**: None
**Status**: Ready for implementation
