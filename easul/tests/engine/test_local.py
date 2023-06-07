import os
import datetime as dt
from easul import *
from easul.engine import local
from easul.examples import create_example_plan, load_data_file


def combine_adm_dt(adm, date_field, time_field, default):
    adm_date = adm[date_field]
    adm_time = adm[time_field]
    # try:
    adm_date = adm_date.date()
    # adm_time = dt.datetime.strptime(adm_time, "%H:%M:%S").time()
    # except TypeError:
    #     return default
    return dt.datetime.combine(adm_date, adm_time.time())


def test_local_engine_works_without_extras():
    import pandas as pd

    adms = DataFrameSource(title="Admissions",
                           data=load_data_file("admission.csv", limit=3),
                           processes=[
                               ParseDate(field_name="date_of_birth", format="%Y%m%d"),
                               ParseDate(field_name="admission_date", format="%Y-%m-%d"),
                               ParseTime(field_name="admission_time", format="%H:%M:%S"),
                               ParseDate(field_name="discharge_date", format="%Y-%m-%d"),
                               ParseTime(field_name="discharge_time", format="%H:%M"),
                               CombineDateTime(date_field="admission_date", time_field="admission_time",
                                               output_field="admission_ts"),
                               CombineDateTime(date_field="discharge_date", time_field="discharge_time",
                                               output_field="discharge_ts")
                           ],
                           reference_field="admission_id",
                           )
    catheter = DataFrameSource(title="Catheter",
                               data=load_data_file("catheter.csv"),
                               reference_field="admission_id",
                               )

    progression = CollatedSource(
        sources={"admissions": adms, "progression": DataFrameSource(title="Progression",
                                                                    data=load_data_file("progression.csv"),
                                                                    reference_field="admission_id"
                                                                    )},
        processes=[
            Age(from_field="date_of_birth", to_field="admission_date", target_field="age"),
            MapValues(mappings={"M": 1, "F": 2}, field="sex")
        ],
        title="Progression",
    )

    engine = local.LocalEngine(
        sources={"admissions": adms, "catheter": catheter, "progression": progression},
        reference_name="admissions",
        start_ts_field="admission_ts",
        end_ts_field="discharge_ts",
    )

    plan = create_example_plan()

    engine.run(plan)
    states, steps = engine.get_outcomes()
