from decimal import Decimal
from scripts.audit_semantics import Specification,aggregate,expected_result,parse_question
from src.evaluation.metrics import compare_results


def test_question_parser_derives_group_metric_and_having_without_sql():
    question='Devuelve exactamente hotel_id y el máximo de tarifa para los grupos de habitaciones cuyo máximo de tarifa supera el promedio global de tarifa de toda la tabla.'
    assert parse_question(question)==Specification('habitaciones','tarifa','max','hotel_id',True)
    assert parse_question('Una pregunta ajena a las plantillas') is None


def test_independent_population_standard_deviation_and_nulls():
    assert aggregate([2,4,4,4,5,5,7,9,None],'stddev_pop')==Decimal(2)
    assert aggregate([None,None],'avg') is None
    assert aggregate([1,1,2,None],'count_distinct')==2
    assert aggregate([2,7,None],'range')==5


def test_having_uses_global_row_average_not_average_of_group_averages():
    rows=[{'g':'a','v':0},{'g':'a','v':0},{'g':'a','v':0},{'g':'b','v':8},{'g':'c','v':3}]
    result=expected_result(Specification('t','v','avg','g',True),rows)
    assert set(result['filas'])=={('b',Decimal(8)),('c',Decimal(3))}


def test_dense_rank_ties_and_negative_aggregate_control():
    rows=[{'id':1,'g':'a','v':4},{'id':2,'g':'a','v':4},{'id':3,'g':'b','v':1}]
    ranks=expected_result(Specification('t','v','dense_rank'),rows)
    assert ranks['filas']==[(1,4,1),(2,4,1),(3,1,2)]
    correct=expected_result(Specification('t','v','avg','g'),rows)
    wrong=expected_result(Specification('t','v','sum','g'),rows)
    assert not compare_results(correct,wrong)
