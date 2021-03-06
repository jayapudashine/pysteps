"""
Testing helper functions
=======================

Collection of helper functions for the testing suite.
"""
import numpy as np
import pytest
from datetime import datetime

import pysteps as stp
from pysteps import io, rcparams, utils
from pysteps.utils import aggregate_fields_space

_reference_dates = dict()
_reference_dates["bom"] = datetime.strptime("2018/06/16 1000", "%Y/%m/%d %H%M")
_reference_dates["fmi"] = datetime.strptime("2016/09/28 1600", "%Y/%m/%d %H%M")
_reference_dates["knmi"] = datetime.strptime("2010/08/26 0000", "%Y/%m/%d %H%M")
_reference_dates["mch"] = datetime.strptime("2015/05/15 1630", "%Y/%m/%d %H%M")
_reference_dates["opera"] = datetime.strptime("2018/08/24 1800", "%Y/%m/%d %H%M")
_reference_dates["saf"] = datetime.strptime("2018/06/01 0700", "%Y/%m/%d %H%M")


def get_precipitation_fields(num_prev_files=0,
                             num_next_files=0,
                             return_raw=False,
                             metadata=False,
                             upscale=None,
                             source="mch"):
    """
    Get a precipitation field from the archive to be used as reference.

    Source: bom
    Reference time: 2018/06/16 10000 UTC

    Source: fmi
    Reference time: 2016/09/28 1600 UTC

    Source: knmi
    Reference time: 2010/08/26 0000 UTC

    Source: mch
    Reference time: 2015/05/15 1630 UTC

    Source: opera
    Reference time: 2018/08/24 1800 UTC

    Source: saf
    Reference time: 2018/06/01 0700 UTC

    Parameters
    ----------

    num_prev_files: int, optional
        Number of previous times (files) to return with respect to the
        reference time.

    num_next_files: int, optional
        Number of future times (files) to return with respect to the
        reference time.

    return_raw: bool, optional
        Do not preprocess the precipitation fields. False by default.
        The pre-processing steps are: 1) Convert to mm/h,
        2) Mask invalid values, 3) Log-transform the data [dBR].

    metadata: bool, optional
        If True, also return file metadata.

    upscale: float or None, optional
        Upscale fields in space during the pre-processing steps.
        If it is None, the precipitation field is not
        modified.
        If it is a float, represents the length of the space window that is
        used to upscale the fields.

    source: {"bom", "fmi" , "knmi", "mch", "opera", "saf"}, optional
        Name of the data source to be used.

    Returns
    -------
    reference_field : array

    metadata : dict


    """

    if source == "bom":
        pytest.importorskip("netCDF4")

    if source == "fmi":
        pytest.importorskip("pyproj")

    if source == "knmi":
        pytest.importorskip("h5py")

    if source == "mch":
        pytest.importorskip("PIL")

    if source == "opera":
        pytest.importorskip("h5py")

    if source == "saf":
        pytest.importorskip("netCDF4")

    try:
        date = _reference_dates[source]
    except KeyError:
        raise ValueError(f"Unknown source name '{source}'\n"
                         "The available data sources are: "
                         f"{str(list(_reference_dates.keys()))}")

    data_source = rcparams.data_sources[source]
    root_path = data_source["root_path"]
    path_fmt = data_source["path_fmt"]
    fn_pattern = data_source["fn_pattern"]
    fn_ext = data_source["fn_ext"]
    importer_name = data_source["importer"]
    importer_kwargs = data_source["importer_kwargs"]
    timestep = data_source["timestep"]

    # Find the input files from the archive
    fns = io.archive.find_by_date(date,
                                  root_path,
                                  path_fmt,
                                  fn_pattern,
                                  fn_ext,
                                  timestep=timestep,
                                  num_prev_files=num_prev_files,
                                  num_next_files=num_next_files)

    # Read the radar composites
    importer = io.get_method(importer_name, "importer")
    reference_field, __, ref_metadata = io.read_timeseries(fns, importer,
                                                           **importer_kwargs)

    if not return_raw:

        if (num_prev_files == 0) and (num_next_files == 0):
            # Remove time dimension
            reference_field = np.squeeze(reference_field)

        # Convert to mm/h
        reference_field, ref_metadata = stp.utils.to_rainrate(reference_field,
                                                              ref_metadata)

        # Upscale data to 2 km
        reference_field, ref_metadata = aggregate_fields_space(reference_field,
                                                               ref_metadata,
                                                               upscale)

        # Mask invalid values
        reference_field = np.ma.masked_invalid(reference_field)

        # Log-transform the data [dBR]
        reference_field, ref_metadata = stp.utils.dB_transform(reference_field,
                                                               ref_metadata,
                                                               threshold=0.1,
                                                               zerovalue=-15.0)

        # Set missing values with the fill value
        np.ma.set_fill_value(reference_field, -15.0)
        reference_field.data[reference_field.mask] = -15.0

    if metadata:
        return reference_field, ref_metadata

    return reference_field


def smart_assert(actual_value, expected, tolerance=None):
    """
    Assert by equality for non-numeric values, or by approximation otherwise.

    If the precision keyword is None, assert by equality.
    When the precision is not None, assert that two numeric values
    (or two sets of numbers) are equal to each other within the tolerance.
    """

    if tolerance is None:
        assert actual_value == expected
    else:
        # Compare numbers up to a certain precision
        assert actual_value == pytest.approx(expected,
                                             rel=tolerance,
                                             abs=tolerance,
                                             nan_ok=True,
                                             )
