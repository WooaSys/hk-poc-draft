"""데이터 검증 모듈 - 데이터 품질 검증 기능 제공."""

from typing import Dict, List
import pandas as pd


def validate_delivery_data(df: pd.DataFrame) -> Dict[str, any]:
    """배송 실적 데이터 검증."""
    errors = []
    warnings = []
    stats = {
        "total_rows": len(df),
        "missing_dates": 0,
        "negative_costs": 0,
        "zero_quantities": 0
    }
    
    required_cols = ["Shipment No.", "Delivery No.", "Actual G/I Date"]
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"필수 컬럼 없음: {col}")
    
    if "Actual G/I Date" in df.columns:
        stats["missing_dates"] = df["Actual G/I Date"].isna().sum()
        if stats["missing_dates"] > 0:
            warnings.append(f"날짜 결측치: {stats['missing_dates']}건")
    
    if "Cost of Shipment" in df.columns:
        cost_numeric = pd.to_numeric(df["Cost of Shipment"], errors="coerce")
        stats["negative_costs"] = (cost_numeric < 0).sum()
        if stats["negative_costs"] > 0:
            errors.append(f"음수 운송비: {stats['negative_costs']}건")
    
    if "Q'ty" in df.columns:
        qty_numeric = pd.to_numeric(df["Q'ty"], errors="coerce")
        stats["zero_quantities"] = (qty_numeric == 0).sum()
        if stats["zero_quantities"] > 0:
            warnings.append(f"0 수량: {stats['zero_quantities']}건")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }


def validate_transport_data(df: pd.DataFrame) -> Dict[str, any]:
    """수송 실적 데이터 검증."""
    errors = []
    warnings = []
    stats = {
        "total_rows": len(df),
        "missing_dates": 0,
        "missing_quantities": 0
    }
    
    if "G/R Date" in df.columns:
        stats["missing_dates"] = df["G/R Date"].isna().sum()
    
    qty_col = " Delivery quantity "
    if qty_col in df.columns:
        stats["missing_quantities"] = df[qty_col].isna().sum()
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }


def validate_price_table(price_long: pd.DataFrame) -> Dict[str, any]:
    """단가표 데이터 검증."""
    errors = []
    warnings = []
    
    null_prices = price_long["price"].isna().sum()
    if null_prices > 0:
        warnings.append(f"단가 없음: {null_prices}건")
    
    negative_prices = (price_long["price"] < 0).sum()
    if negative_prices > 0:
        errors.append(f"음수 단가: {negative_prices}건")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "unique_rdc": price_long["rdc"].nunique() if "rdc" in price_long.columns else 0,
        "unique_ton": price_long["ton"].nunique() if "ton" in price_long.columns else 0
    }


def check_data_consistency(
    delivery_df: pd.DataFrame,
    transport_df: pd.DataFrame
) -> Dict[str, any]:
    """배송-수송 데이터 일관성 검증."""
    issues = []
    
    delivery_count = len(delivery_df)
    transport_count = len(transport_df)
    
    if delivery_count != transport_count:
        issues.append(
            f"행 수 불일치: 배송={delivery_count}, 수송={transport_count}"
        )
    
    return {
        "consistent": len(issues) == 0,
        "issues": issues,
        "delivery_count": delivery_count,
        "transport_count": transport_count
    }