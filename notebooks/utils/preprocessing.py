"""데이터 전처리 모듈 - 데이터 정제 및 변환 기능 제공."""

from typing import Tuple
import pandas as pd
import numpy as np


def clean_delivery_data(df: pd.DataFrame) -> pd.DataFrame:
    """배송 실적 데이터 정제.
    
    - 컬럼명 정리
    - 날짜 컬럼 변환
    - 결측치 처리
    """
    df = df.copy()
    
    date_cols = [
        "Shipment Making Date", "Actual G/I Date",
        "Picking Start", "Picking Ending",
        "Loading Start", "Loading Ending",
        "Real G/I", "Arrival by Delivery"
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    numeric_cols = ["Q'ty", "Cost of Shipment"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    if "Distance by Shipment" in df.columns:
        df["distance_km"] = (
            df["Distance by Shipment"]
            .astype(str)
            .str.replace(" km", "", regex=False)
            .str.replace(",", "")
        )
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    
    return df


def clean_transport_data(df: pd.DataFrame) -> pd.DataFrame:
    """수송 실적 데이터 정제."""
    df = df.copy()
    
    if "G/R Date" in df.columns:
        df["G/R Date"] = pd.to_datetime(df["G/R Date"], errors="coerce")
    
    qty_col = " Delivery quantity "
    if qty_col in df.columns:
        df["quantity"] = pd.to_numeric(df[qty_col], errors="coerce")
    
    cost_col = "기준욱반비"
    if cost_col in df.columns:
        df["cost"] = (
            df[cost_col]
            .astype(str)
            .str.replace(",", "")
        )
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    
    return df


def parse_price_table(feb_df: pd.DataFrame, nov_df: pd.DataFrame) -> pd.DataFrame:
    """단가표 데이터를 long format으로 변환.
    
    Returns:
        거리별, RDC별, 톤수별 단가가 행으로 펼쳐진 DataFrame
    """
    def melt_price(df, month):
        df = df.copy()
        df = df.rename(columns={df.columns[0]: "no", df.columns[1]: "distance_range"})
        
        melted = pd.melt(
            df,
            id_vars=["no", "distance_range"],
            var_name="rdc_ton",
            value_name="price"
        )
        
        parts = melted["rdc_ton"].str.extract(r'(\w+RDC)\s+(\d+\.?\d*)T?')
        melted["rdc"] = parts[0]
        melted["ton"] = parts[1]
        melted["month"] = month
        
        melted["price"] = (
            melted["price"]
            .astype(str)
            .str.replace(",", "")
            .str.replace(" ", "")
            .replace("", np.nan)
        )
        melted["price"] = pd.to_numeric(melted["price"], errors="coerce")
        
        return melted[["month", "rdc", "ton", "distance_range", "price"]]
    
    feb_melted = melt_price(feb_df, "2025-02")
    nov_melted = melt_price(nov_df, "2025-11")
    
    return pd.concat([feb_melted, nov_melted], ignore_index=True)


def calculate_distance_category(distance_km: pd.Series) -> pd.Series:
    """거리(km)를 단가표 구간으로 분류."""
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
            120, 140, 160, 180, 200, 230, 260, 290, 320, 350, 380, 410]
    labels = [
        "1~10 km", "11~20 km", "21~30 km", "31~40 km", "41~50 km",
        "51~60 km", "61~70 km", "71~80 km", "81~90 km", "91~100 km",
        "101~120 km", "121~140 km", "141~160 km", "161~180 km",
        "181~200 km", "201~230 km", "231~260 km", "261~290 km",
        "291~320 km", "321~350 km", "351~380 km", "381~410 km"
    ]
    
    return pd.cut(distance_km, bins=bins, labels=labels, right=True)


def merge_delivery_with_price(
    delivery_df: pd.DataFrame,
    price_df: pd.DataFrame
) -> pd.DataFrame:
    """배송 데이터와 단가표를 병합하여 예상 운송비 계산."""
    delivery_df = delivery_df.copy()
    
    if "distance_category" not in delivery_df.columns:
        delivery_df["distance_category"] = calculate_distance_category(
            delivery_df["distance_km"]
        )
    
    merged = delivery_df.merge(
        price_df,
        left_on=["G/I Plant Name", "Type of Truck by shipment", "distance_category"],
        right_on=["rdc", "ton", "distance_range"],
        how="left"
    )
    
    return merged