**Deprecated: GEOS added native support for MakeValid and Shapely v1.8.0 now includes this https://github.com/Toblerity/Shapely/pull/895** 

makevalid
=========

PostGIS ST_MakeValid equivalent using Shapely

### Installation
```bash
python setup.py install
```

### Run Tests
```bash
python tests/test_validity.py
```

### Sample Usage
Refer to tests/test_validity.py for sample usage.

### Link to PostGIS
https://github.com/postgis/postgis
- For specific functionality that was ported: https://github.com/postgis/postgis/blob/svn-trunk/liblwgeom/lwgeom_geos_clean.c#L361
