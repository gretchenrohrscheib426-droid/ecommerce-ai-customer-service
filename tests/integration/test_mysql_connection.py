import pytest

pytestmark = pytest.mark.integration


def test_real_select_only_reader(real_mysql):
    import pymysql

    with real_mysql.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS n FROM spu_info")
        assert cursor.fetchone()["n"] == 3
        with pytest.raises(pymysql.err.OperationalError) as denied:
            cursor.execute("UPDATE spu_info SET spu_name=spu_name WHERE 1=0")
        assert denied.value.args[0] == 1142
