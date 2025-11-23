# fin68_findata.py

from __future__ import annotations
from typing import Optional

import pandas as pd
import vectorbtpro as vbt
from sqlalchemy.engine import Engine

from manage_engine import engine_stockDB  # Engine Postgres bạn đang dùng


def get_fin_symbol(
    symbol: str,
    *,
    engine: Optional[Engine] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Tương tự get_yf_symbol trong docs, nhưng đọc từ Postgres.

    - symbol: mã cổ phiếu, ví dụ 'HPG'
    - start, end: có thể là 'YYYY-MM-DD', 'YYYY-MM-DD UTC', Timestamp,...
      (VBT sẽ hỗ trợ convert về datetime)
    """

    eng = engine or engine_stockDB

    # Chuẩn docs: convert start/end sang datetime cục bộ nếu có
    # (ở đây chủ yếu để bạn giữ cách dùng giống YFData)
    start_str = None
    end_str = None

    if start is not None:
        start_dt = vbt.local_datetime(start)
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")

    if end is not None:
        end_dt = vbt.local_datetime(end)
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    safe_symbol = symbol.replace("'", "''")

    sql = f"""
        SELECT
            "DateTime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        FROM eod.eod_stock_v2
        WHERE "ticker" = '{safe_symbol}'
    """

    if start_str is not None:
        sql += f""" AND "DateTime" >= '{start_str}'"""
    if end_str is not None:
        sql += f""" AND "DateTime" <= '{end_str}'"""

    sql += """ ORDER BY "DateTime" ASC"""

    # Trả về DataFrame giống hệt get_yf_symbol (index = DateTime)
    df = pd.read_sql_query(
        sql,
        eng,
        parse_dates=["DateTime"],
        index_col="DateTime",
    )

    return df
class FINData(vbt.Data):
    """FINData: Data class đọc OHLCV từ Postgres Fin68.

    Dùng đúng pattern YFData trong docs:
    - override fetch_symbol
    - dùng Data.pull để lấy nhiều symbol
    """

    # Engine mặc định, vẫn có thể override bằng tham số engine=...
    default_engine: Engine = engine_stockDB

    @classmethod
    def fetch_symbol(cls, symbol: str, **kwargs):
        """
        Hàm bắt buộc phải override theo docs.

        Data.pull(...) sẽ gọi FINData.fetch_symbol cho từng symbol.
        Ở đây mình forward sang get_fin_symbol(...).
        """

        # Cho phép truyền engine=... trong FINData.pull(...),
        # nếu không có thì dùng default_engine
        engine = kwargs.pop("engine", cls.default_engine)

        return get_fin_symbol(
            symbol,
            engine=engine,
            **kwargs,
        )