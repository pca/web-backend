from wca.models import Result


def test_result_has_indexes_for_single_and_average_ranking_queries():
    index_names = {index.name for index in Result._meta.indexes}

    assert {
        "wca_res_person_evt_best_idx",
        "wca_res_evt_ctry_best_person",
        "wca_res_person_evt_avg_idx",
        "wca_res_evt_ctry_avg_person",
    } <= index_names
