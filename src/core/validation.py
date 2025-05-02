"""
Data validation module for profit and loss reports.

This module provides functions for validating Excel files
and ensuring they contain valid profit and loss data.
"""

import pandas as pd
import os
import re
from typing import Dict, List, Tuple, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, ValidationError

from src.utils.logger import app_logger

# Configure module-specific logger
logger = app_logger.getChild('validation')


class ExcelFileValidationError(Exception):
    """Exception raised for errors during Excel file validation."""
    pass


class ValidationResult(BaseModel):
    """Model for validation results."""
    is_valid: bool = Field(True, description="Whether the file is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")


class ProfitLossExcelValidator(BaseModel):
    """
    Validator for profit and loss Excel files.
    
    This model validates Excel files to ensure they contain valid profit and loss data.
    """
    file_path: str = Field(..., description="Path to the Excel file")
    min_rows: int = Field(10, description="Minimum number of rows required")
    min_cols: int = Field(2, description="Minimum number of columns required")
    required_keywords: List[str] = Field(
        default_factory=lambda: [
            "profit", "loss", "income", "expense", "revenue", "sales"
        ],
        description="At least one of these keywords must be present in the file"
    )
    section_keywords: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "income": ["trading income", "revenue", "sales", "income", "operating revenue"],
            "expenses": ["operating expenses", "expenses", "overhead", "indirect costs"],
            "profit": ["gross profit", "net profit", "net income", "profit for the period"]
        },
        description="Keywords to identify essential P&L sections"
    )
    
    @field_validator('file_path')
    @classmethod
    def file_must_exist(cls, v):
        """Validate that the file exists and is an Excel file."""
        if not os.path.exists(v):
            raise ValueError(f"File not found: {v}")
        
        if not v.lower().endswith(('.xlsx', '.xls')):
            raise ValueError(f"File is not an Excel file: {v}")
        
        return v
    
    def validate_file_structure(self, df: pd.DataFrame) -> List[str]:
        """
        Validate the basic structure of the Excel file.
        
        Args:
            df: DataFrame containing the Excel data
            
        Returns:
            List of error messages, empty if valid
        """
        errors = []
        
        # Check minimum dimensions
        if len(df) < self.min_rows:
            errors.append(f"File contains only {len(df)} rows, minimum required is {self.min_rows}")
        
        if len(df.columns) < self.min_cols:
            errors.append(f"File contains only {len(df.columns)} columns, minimum required is {self.min_cols}")
        
        # Check for empty dataframe
        if df.empty:
            errors.append("File contains no data")
            
        # Check for too many NaN values (>80% of cells)
        nan_percentage = df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100
        if nan_percentage > 80:
            errors.append(f"File contains too many empty cells ({nan_percentage:.1f}%)")
            
        return errors
    
    def validate_content(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Validate the content of the Excel file to ensure it's a P&L report.
        
        Args:
            df: DataFrame containing the Excel data
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for required keywords
        found_keywords = []
        for i in range(min(20, len(df))):  # Check first 20 rows
            row_str = ' '.join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
            for keyword in self.required_keywords:
                if keyword in row_str:
                    found_keywords.append(keyword)
        
        if not found_keywords:
            errors.append(
                "File does not appear to be a profit and loss report. "
                f"None of the required keywords ({', '.join(self.required_keywords)}) were found."
            )
        
        # Check for essential P&L sections
        found_sections = {section: False for section in self.section_keywords}
        
        for i in range(min(30, len(df))):  # Check first 30 rows
            row_str = ' '.join(str(x).lower() for x in df.iloc[i] if pd.notna(x))
            for section, keywords in self.section_keywords.items():
                if any(keyword in row_str for keyword in keywords):
                    found_sections[section] = True
        
        missing_sections = [section for section, found in found_sections.items() if not found]
        if missing_sections:
            warnings.append(
                f"Could not identify the following essential sections: {', '.join(missing_sections)}. "
                "The analysis may be incomplete."
            )
        
        # Check for numeric data
        numeric_cols = 0
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, (int, float))).any():
                numeric_cols += 1
        
        if numeric_cols == 0:
            errors.append("No numeric data found in the file. A profit and loss report should contain financial figures.")
        
        return errors, warnings
    
    def validate(self) -> ValidationResult:
        """
        Validate the Excel file.
        
        Returns:
            ValidationResult object with validation results
        
        Raises:
            ExcelFileValidationError: If the file cannot be read
        """
        logger.info(f"Validating Excel file: {self.file_path}")
        
        try:
            # Try to read the Excel file
            df = pd.read_excel(self.file_path)
            
            # Validate structure
            structure_errors = self.validate_file_structure(df)
            
            # Validate content
            content_errors, warnings = self.validate_content(df)
            
            # Combine all errors
            all_errors = structure_errors + content_errors
            
            # Create validation result
            result = ValidationResult(
                is_valid=len(all_errors) == 0,
                errors=all_errors,
                warnings=warnings
            )
            
            if result.is_valid:
                logger.info(f"File validation successful: {self.file_path}")
                if result.warnings:
                    logger.warning(f"Validation warnings: {result.warnings}")
            else:
                logger.error(f"File validation failed: {self.file_path}")
                logger.error(f"Validation errors: {result.errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating Excel file: {str(e)}")
            raise ExcelFileValidationError(f"Error reading Excel file: {str(e)}")


def validate_excel_file(file_path: str) -> ValidationResult:
    """
    Validate an Excel file to ensure it contains valid profit and loss data.
    
    This is the main function to be used by the application to validate Excel files.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        ValidationResult object with validation results
        
    Raises:
        ExcelFileValidationError: If the file cannot be read or validated
    """
    try:
        validator = ProfitLossExcelValidator(file_path=file_path)
        return validator.validate()
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid file: {str(e)}"]
        )
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        raise ExcelFileValidationError(f"Error validating Excel file: {str(e)}")
