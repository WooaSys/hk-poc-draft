"""
한국타이어 POC 분석 유틸리티 모듈

주요 기능:
- 데이터 로딩 (CSV, Shapefile)
- 데이터 전처리 및 정제
n- 데이터 검증
- 시각화 헬퍼
"""

from .data_loader import (
    load_delivery_data,
    load_transport_data,
    load_price_table,
    load_shapefile,
    load_sigungu_shapefile,
    load_delivery_master,
    load_region_mapping,
    load_rdc_locations,
    load_all_raw_data
)

from .preprocessing import (
    clean_delivery_data,
    clean_transport_data,
    parse_price_table,
    merge_delivery_with_price,
    calculate_distance_category
)

from .validators import (
    validate_delivery_data,
    validate_transport_data,
    validate_price_table,
    check_data_consistency
)

from .visualization import (
    plot_delivery_trend,
    plot_cost_by_distance,
    plot_truck_utilization,
    create_map_visualization
)

__version__ = "0.1.0"
__all__ = [
    # Data Loader
    "load_delivery_data",
    "load_transport_data",
    "load_price_table",
    "load_shapefile",
    "load_sigungu_shapefile",
    "load_delivery_master",
    "load_region_mapping",
    "load_rdc_locations",
    "load_all_raw_data",
    # Preprocessing
    "clean_delivery_data",
    "clean_transport_data",
    "parse_price_table",
    "merge_delivery_with_price",
    "calculate_distance_category",
    # Validators
    "validate_delivery_data",
    "validate_transport_data",
    "validate_price_table",
    "check_data_consistency",
    # Visualization
    "plot_delivery_trend",
    "plot_cost_by_distance",
    "plot_truck_utilization",
    "create_map_visualization"
]