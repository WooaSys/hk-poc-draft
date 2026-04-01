"""데이터 로딩 모듈 - CSV 및 Shapefile 로딩 기능 제공."""

from pathlib import Path
from typing import Optional, Dict, Tuple
import pandas as pd
import geopandas as gpd


def get_raw_data_path() -> Path:
    """raw_data 디렉토리 경로 반환."""
    return Path("../raw_data").resolve()


def load_delivery_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """배송 실적 데이터 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        배송 실적 DataFrame
    """
    if file_path is None:
        file_path = get_raw_data_path() / "1.업체 공유용_배송 실적_2025년 2월 11월_20260317.csv"
    
    df = pd.read_csv(file_path, skiprows=3)
    return df


def load_transport_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """수송 실적 데이터 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        수송 실적 DataFrame
    """
    if file_path is None:
        file_path = get_raw_data_path() / "2.업체 공유용_수송 실적_2025년 2월 11월_20260317.csv"
    
    df = pd.read_csv(file_path)
    return df


def load_price_table(file_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """배송 단가표 데이터 로드.
    
    2025년 2월과 11월 데이터를 각각 반환.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        (feb_df, nov_df) - 2월과 11월 단가표 DataFrame 튜플
    """
    if file_path is None:
        file_path = get_raw_data_path() / "3.업체 공유용_배송 단가표_2025년 2월 11월__20260317.csv"
    
    raw_df = pd.read_csv(file_path, header=None)
    
    feb_df = raw_df.iloc[0:23].copy()
    feb_df.columns = raw_df.iloc[2]
    feb_df = feb_df.iloc[3:].reset_index(drop=True)
    
    nov_df = raw_df.iloc[25:49].copy()
    nov_df.columns = raw_df.iloc[27]
    nov_df = nov_df.iloc[2:].reset_index(drop=True)
    
    return feb_df, nov_df


def load_shapefile(file_path: Optional[str] = None) -> gpd.GeoDataFrame:
    """행정동 Shapefile 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        행정동 GeoDataFrame
    """
    if file_path is None:
        file_path = get_raw_data_path() / "map" / "BND_ADM_DONG_PG.shp"
    
    gdf = gpd.read_file(file_path)
    return gdf


def load_sigungu_shapefile(file_path: Optional[str] = None) -> gpd.GeoDataFrame:
    """시군구 Shapefile 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        시군구 GeoDataFrame
    """
    if file_path is None:
        file_path = get_raw_data_path() / "map" / "BND_SIGUNGU_PG.shp"
    
    gdf = gpd.read_file(file_path)
    return gdf


def load_delivery_master(file_path: Optional[str] = None) -> pd.DataFrame:
    """배송지 마스터 데이터 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        배송지 마스터 DataFrame
    """
    if file_path is None:
        file_path = Path("../00_draft").resolve() / "배송지_마스터.csv"
    
    df = pd.read_csv(file_path)
    return df


def load_region_mapping(file_path: Optional[str] = None) -> pd.DataFrame:
    """배송지코드 지역 매핑 데이터 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        배송지코드 지역매핑 DataFrame
    """
    if file_path is None:
        file_path = Path("../00_draft").resolve() / "배송지코드_지역매핑.csv"
    
    df = pd.read_csv(file_path)
    return df


def load_rdc_locations(file_path: Optional[str] = None) -> pd.DataFrame:
    """물류센터 위치 데이터 로드.
    
    Args:
        file_path: 파일 경로 (None이면 기본 경로 사용)
        
    Returns:
        물류센터 위치 DataFrame
    """
    if file_path is None:
        file_path = Path("../00_draft").resolve() / "물류센터_위치.csv"
    
    df = pd.read_csv(file_path)
    return df


def load_all_raw_data() -> Dict[str, object]:
    """모든 원본 데이터 로드.
    
    Returns:
        {
            'delivery': 배송 실적 DataFrame,
            'transport': 수송 실적 DataFrame,
            'price_feb': 2월 단가표 DataFrame,
            'price_nov': 11월 단가표 DataFrame,
            'shapefile_dong': 행정동 GeoDataFrame,
            'shapefile_sigungu': 시군구 GeoDataFrame,
            'delivery_master': 배송지 마스터 DataFrame,
            'region_mapping': 배송지코드 지역매핑 DataFrame,
            'rdc_locations': 물류센터 위치 DataFrame
        }
    """
    return {
        "delivery": load_delivery_data(),
        "transport": load_transport_data(),
        "price_feb": load_price_table()[0],
        "price_nov": load_price_table()[1],
        "shapefile_dong": load_shapefile(),
        "shapefile_sigungu": load_sigungu_shapefile(),
        "delivery_master": load_delivery_master(),
        "region_mapping": load_region_mapping(),
        "rdc_locations": load_rdc_locations()
    }