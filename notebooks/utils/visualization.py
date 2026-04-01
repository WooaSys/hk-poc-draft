"""시각화 모듈 - 데이터 시각ization 기능 제공."""

from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def setup_korean_font():
    """한글 폰트 설정."""
    plt.rcParams["font.family"] = ["AppleGothic", "Malgun Gothic", "sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False


def plot_delivery_trend(df: pd.DataFrame, date_col: str = "Actual G/I Date"):
    """배송 실적 추이 시각화."""
    setup_korean_font()
    
    daily = df.groupby(df[date_col].dt.date).size()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    daily.plot(ax=ax)
    ax.set_title("일별 배송 건수 추이")
    ax.set_xlabel("날짜")
    ax.set_ylabel("건수")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig


def plot_cost_by_distance(df: pd.DataFrame):
    """거리별 운송비 분포 시각화."""
    setup_korean_font()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x="Type of Truck by shipment", y="Cost of Shipment", ax=ax)
    ax.set_title("차량 톤수별 운송비 분포")
    ax.set_xlabel("차량 톤수")
    ax.set_ylabel("운송비")
    plt.tight_layout()
    return fig


def plot_truck_utilization(df: pd.DataFrame):
    """트럭 톤수별 활용 현황 시각화."""
    setup_korean_font()
    
    truck_counts = df["Type of Truck by shipment"].value_counts()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    truck_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%")
    ax.set_title("차량 톤수별 비중")
    ax.set_ylabel("")
    plt.tight_layout()
    return fig


def create_map_visualization(gdf, delivery_df: Optional[pd.DataFrame] = None):
    """지도 시각화 생성."""
    setup_korean_font()
    
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(ax=ax, color="lightblue", edgecolor="black", linewidth=0.5)
    
    if delivery_df is not None and "광역도시" in delivery_df.columns:
        city_counts = delivery_df["광역도시"].value_counts()
        ax.set_title(f"배송 현황 (총 {len(delivery_df)}건)")
    else:
        ax.set_title("행정동 지도")
    
    plt.tight_layout()
    return fig