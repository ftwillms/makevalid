import shapely
from shapely.geometry import Polygon, Point
from shapely.ops import polygonize, cascaded_union

import shapely.speedups
if shapely.speedups.available:
    shapely.speedups.enable()

from rtree import index
import math

import logging
logger = logging.getLogger(__name__)


def make_geom_valid(polygon_geom):
    """
    Given a polygon object, attempt to make it valid via the
    same logic provided from ST_MakeValid in PostGIS.
    """
    if polygon_geom.is_valid:
        return polygon_geom
    elif polygon_geom.is_empty:
        logger.debug("Empty area!")
        return None
    else:
        logger.debug("Attempting to make polygon valid!")
    #
    cut_edges = polygon_geom.boundary.union(get_first_point(polygon_geom.boundary))
    # Empty polygon to start off with.
    geos_area = Polygon()
    while hasattr(cut_edges, 'geoms'):
        new_area = build_area(cut_edges)
        if new_area.is_empty:
            logger.debug("No more rings can be built with these edges...")
            break
        new_area_bound = new_area.boundary
        symdif = geos_area.symmetric_difference(new_area)
        if not symdif:
            logger.warn("No symdif!")
        geos_area = symdif
        new_cut_edges = cut_edges.difference(new_area_bound)
        cut_edges = new_cut_edges

    if geos_area.is_empty:
        logger.warn("Failed to make valid!")
        return None
    return geos_area


def build_area(noded_lines):
    results = []
    for p in polygonize(noded_lines):
        results.append(p)
    if len(results) == 1:
        return results[0]
    results.sort(key=lambda x: x.envelope.area, reverse=True)
    faces_idx = index.Index()
    faces_idx_count = 0
    for geom in results:
        faces_idx.insert(faces_idx_count, geom.bounds)
        faces_idx_count += 1
    # f1 -> face one
    # f2 -> face two
    for i, f1 in enumerate(results):
        for interior in f1.interiors:
            for j in faces_idx.intersection(interior.bounds):
                if j == i:
                    continue
                f2 = results[j]
                if hasattr(f2, 'parent'):
                    continue
                else:
                    f2_exterior = f2.exterior
                    if len(f2_exterior.coords) == len(interior.coords) and f2_exterior.equals(interior):
                        f2.parent = f1
                        break

    # Only return the faces with "even ancestors"
    out_results = []
    for result in results:
        if count_faces(result) % 2 == 0:
            out_results.append(result)

    # Run a single overlay operation to dissolve shared edges.
    out_results = cascaded_union(out_results)
    return out_results


def count_faces(geom):
    """
    During build area, parents are assigned to different results
    to determine which polygons are holes and which aren't.
    """
    count = 0
    while (hasattr(geom, 'parent')):
        geom = geom.parent
        count += 1
    return count


def get_first_point(geometry):
    """
    Return the 1st point of a geometry.
    """
    if hasattr(geometry, 'geoms'):
        return get_first_point(geometry.geoms[0])
    else:
        if isinstance(geometry, Polygon):
            return get_first_point(geometry.exterior)
        return Point(geometry.coords[0])


def remove_geom_spikes(polygon_geom):
    logger.debug("Attempting to remove spikes from geometry...")
    logger.debug("Length of interiors: %s"
                 % len(polygon_geom.interiors))

    if polygon_geom.type != 'Polygon':
        logger.warn("Cannot remove geometry spikes currently from %s" % polygon_geom.type)
        return polygon_geom

    new_interiors = []
    for ring in polygon_geom.interiors:
        new_interior = spike_remover(ring)
        if new_interior:
            new_interiors.append(new_interior)
        else:
            logger.debug("New interior came back None")
    logger.debug("Converting the geometry...")
    new_geometry = shapely.geometry.asPolygon(polygon_geom.exterior,
                                              new_interiors)
    if not new_geometry or new_geometry.is_empty:
        logger.warn("Something happened while trying to remove spikes from this polygon!")
        return polygon_geom
    return new_geometry


def spike_remover(linear_ring):
    """
    Returns the linear ring with any spikes removed.
    If the ring contains less than 3 points or if the
    area of the ring is 0, None is returned.
    """
    coords = list(linear_ring.coords)
    i = 0  # current index
    while True:
        if len(coords) <= 3:
            logger.info("Coords length less than 3!")
            return None
        try:
            point_a = coords[i]
            point_b = coords[i+1]
            # if (i + 3) > len(coords):
            #     point_c = coords[0]
            # else:
            point_c = coords[i+2]
        except Exception as e:
            logger.error(e)
            logger.info("Index count: %s" % i)
            logger.info("Length of coords: %s" % len(coords))
            raise
        angle = find_angle(point_a, point_b, point_c)
        abs_angle = abs(angle)
        if abs_angle < 1.0:
            # Remove the bad point, don't increment!
            logger.warn("Found a super small angle (%s), removing point!"
                        % abs_angle)
            coords.remove(point_b)
        else:
            if (i + 4) > len(coords):
                break
            # Everything is good here, move along.
            i += 1

    new_ring = shapely.geometry.Polygon(coords)

    # TODO: What if the area is really, really, really small?
    if new_ring.area <= 0:
        logger.debug("The new ring has a 0 area!")
        logger.debug("The coords: %s" % str(coords))
        return None
    else:
        return new_ring.exterior


def find_angle(point_a, point_b, point_c):
    """
    Returns the degrees of the angle between three points
    """
    return math.degrees(
        math.atan2(
            point_a[0] - point_b[0],
            point_a[1] - point_b[1]
        ) -
        math.atan2(
            point_c[0] - point_b[0],
            point_c[1] - point_b[1]
        )
    )


def normalize_geometry(geometry, make_valid=False, remove_spikes=False,
                       perimeter_threshold=0.90):
    """
    By normalize, explode any collections or multipolygons into a list
    of individual polygons.
    """

    new_geom = []

    if geometry is not None:
        # Initial check to see if its an individual polygon
        # and needs to be cleaned
        if geometry.type == 'Polygon':
            before_perim = geometry.length
            if make_valid is True:
                # Make valid will return if the geometry is already valid.
                geometry = make_geom_valid(geometry)
                if not geometry:
                    logger.warn("Geometry made valid came back empty! Length before: %s" % before_perim)
                    return []
                # geometry = geometry.buffer(0)
                # after_perim = geometry.length
                # logger.debug("Perimeter before: %s, after: %s"
                #              % (before_perim, after_perim))
                # if not perimeter_test(before_perim, after_perim):
                #     geometry = make_valid(geometry)
                    # raise ValueError("Polygon perimeter less than threshold "
                    #                  "after buffer. Before: %s, After: %s"
                    #                  % (before_perim, after_perim))

        if geometry.type == 'MultiPolygon':
            # Is this a multipolygon or if the buffer made it into
            # a multipolyon? Send it back in.
            logger.debug("Found a MultiPolygon")
            for g in geometry:
                new_geom = new_geom + normalize_geometry(g, make_valid,
                                                         remove_spikes)
        elif geometry.type == 'GeometryCollection':
            # Loop through the individual components
            logger.debug("Found a GeometryCollection")
            for g in geometry:
                new_geom = new_geom + normalize_geometry(g, make_valid,
                                                         remove_spikes)
        elif geometry.type == 'Polygon':
            # If the previous polygon doesn't get changed,
            # and it has an area, not empty, and valid...
            # append it!
            if remove_spikes:
                # TODO: What about the exterior?
                logger.debug("removing some spikes...")
                logger.debug("Length of interiors: %s"
                             % len(geometry.interiors))
                new_interiors = []
                for ring in geometry.interiors:
                    new_interior = spike_remover(ring)
                    if new_interior:
                        new_interiors.append(new_interior)
                    else:
                        logger.debug("New interior came back None")
                logger.debug("Converting the geometry...")
                geometry = shapely.geometry.asPolygon(geometry.exterior,
                                                      new_interiors)
            if geometry.area > 0 and not geometry.is_empty:
                if make_valid and not geometry.is_valid:
                    logger.info("Failed to clean geometry!")
                else:
                    # logger.debug("Adding the geometry...")
                    new_geom.append(geometry)

    return new_geom
