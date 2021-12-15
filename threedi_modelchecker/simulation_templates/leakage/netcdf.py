from osgeo import gdal
import h5py
import numpy as np


HUNDERD_YEARS_IN_SECONDS = 100 * 365 * 24 * 60 * 60


def get_epsg(sr):
    """Return EPSG:<code> from a SpatialReference
    """
    key = "GEOGCS" if sr.IsGeographic() else "PROJCS"
    name = sr.GetAuthorityName(key)
    if name != "EPSG":
        return
    code = sr.GetAuthorityCode(key)
    return f"EPSG:{code}"


def geotiff_to_netcdf(path, out):
    """Convert a leakage GeoTIFF to a NetCDF (according to FEWS 2017.02)

    This function writes the minimum amount of fields to be used with
    the 3Di API
    """
    src = gdal.Open(path)
    width = src.RasterXSize
    height = src.RasterYSize
    xoff, dx, _, yoff, _, dy = src.GetGeoTransform()
    assert xoff > 0
    if dy < 0:
        flip_y = True
        dy = -dy
        yoff -= (height * dy)
    else:
        flip_y = False
    band = src.GetRasterBand(1)

    with h5py.File(out, "w") as f:
        f.attrs["title"] = b"leakage"
        f.attrs["institution"] = b"Nelen & Schuurmans"
        f.attrs["source"] = b"Converted from leakage GeoTIFF file"
        f.attrs["fews_implementation_version"] = b"2017.02"
    
        crs = f.create_dataset("crs", shape=(), dtype=np.int32)
        crs.attrs["crs_wkt"] = src.GetProjection().encode()
        crs.attrs["epsg_code"] = get_epsg(src.GetSpatialRef()).encode()

        x = f.create_dataset("x", data=np.arange(xoff, xoff + dx * width, dx))
        y = f.create_dataset("y", data=np.arange(yoff, yoff + dy * height, dy))
        t = f.create_dataset("time", data=np.array([HUNDERD_YEARS_IN_SECONDS], dtype=float))
        t.attrs["units"] = b"seconds since 1970-01-01 00:00:00.0 +0000'"
    
        data = band.ReadAsArray()
        data /= 24.0  # leakage geotiff is in mm/day, convert to mm/hr
        if flip_y:
            data = data[::-1]
        values = f.create_dataset("values", shape=(2, height, width), fillvalue=0.0, dtype=data.dtype)
        values[0] = data 
        values.attrs["units"] = b"mm/hr"
        values.attrs["_FillValue"] = np.array([band.GetNoDataValue()], dtype=data.dtype)

        x.make_scale("x")
        y.make_scale("y")
        t.make_scale("t")
        values.dims[0].attach_scale(t)
        values.dims[1].attach_scale(y)
        values.dims[2].attach_scale(x)
