from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class CollectionMetadata(Base):
    __tablename__ = "collection_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_type = Column(String(20), nullable=False)  # text, number, date, boolean, select, textarea
    field_value = Column(Text, nullable=True)
    field_options = Column(JSON, nullable=True)  # For select fields - array of options
    field_label = Column(String(200), nullable=True)  # Display label for the field
    field_description = Column(Text, nullable=True)  # Help text for the field
    is_required = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)  # Whether field can be searched
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", back_populates="metadata_fields")
    
    def __repr__(self):
        return f"<CollectionMetadata(id={self.id}, collection_id={self.collection_id}, field_name='{self.field_name}', field_type='{self.field_type}')>"
    
    @property
    def formatted_value(self):
        """Return formatted value based on field type"""
        if not self.field_value:
            return None
            
        if self.field_type == "number":
            try:
                return float(self.field_value)
            except (ValueError, TypeError):
                return self.field_value
        elif self.field_type == "boolean":
            return self.field_value.lower() in ("true", "1", "yes", "on")
        elif self.field_type == "date":
            try:
                return datetime.fromisoformat(self.field_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return self.field_value
        else:
            return self.field_value
    
    def set_value(self, value):
        """Set value with proper formatting based on field type"""
        if value is None:
            self.field_value = None
            return
            
        if self.field_type == "number":
            self.field_value = str(value)
        elif self.field_type == "boolean":
            self.field_value = str(bool(value)).lower()
        elif self.field_type == "date":
            if isinstance(value, datetime):
                self.field_value = value.isoformat()
            else:
                self.field_value = str(value)
        else:
            self.field_value = str(value)

