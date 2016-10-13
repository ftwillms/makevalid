import unittest

import logging
import sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

import makevalid


class ValidityTestCases(unittest.TestCase):

    def test_make_valid(self):
        import shapely.wkt
        from shapely.geometry import mapping
        from shapely.geometry import Polygon
        from shapely.geometry import MultiPolygon

        output_results = []
        print("Testing valid, plain polygon...")
        test_poly = shapely.wkt.loads('POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertIsInstance(validated_poly, Polygon)
        self.assertTrue(test_poly.length == validated_poly.length)
        self.assertTrue(test_poly.area == validated_poly.area)
        output_results.append({'properties': {'name': 'plain_poly'}, 'geometry': mapping(validated_poly)})

        print("Testing valid polygon with interior hole...")
        test_poly = shapely.wkt.loads('POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10),(20 30, 35 35, 30 20, 20 30))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertIsInstance(validated_poly, Polygon)
        self.assertTrue(test_poly.length == validated_poly.length)
        self.assertTrue(test_poly.area == validated_poly.area)
        output_results.append({'properties': {'name': 'plain_poly_with_hole'}, 'geometry': mapping(validated_poly)})

        print("Testing invalid missing quadrant polygon...")
        test_poly = shapely.wkt.loads('POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0), (0 0, 0 1, 1 1, 1 0, 0 0))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(validated_poly.area == 4.0)
        output_results.append({'properties': {'name': 'missing_quadrant'}, 'geometry': mapping(validated_poly)})

        print("Testing classic, invalid bowtie polygon...")
        test_poly = shapely.wkt.loads('POLYGON((0 0, 0 10, 10 0, 10 10, 0 0))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertIsInstance(validated_poly, MultiPolygon)
        self.assertTrue(len(validated_poly) == 2)
        self.assertTrue(validated_poly[0].area == validated_poly[1].area)
        output_results.append({'properties': {'name': 'bowtie'}, 'geometry': mapping(validated_poly)})

        print("Testing bowtie with a hole in it!")
        test_poly = shapely.wkt.loads('POLYGON((0 0, 0 10, 10 0, 10 10, 0 0), (9 8, 6 5, 9 2, 9 8))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(len(validated_poly) == 2)
        self.assertTrue(len(validated_poly[0].interiors) == 0)
        self.assertTrue(len(validated_poly[1].interiors) == 1)
        output_results.append({'properties': {'name': 'bowtie_w_hole'}, 'geometry': mapping(validated_poly)})

        print("Testing hole outside shell...")
        test_poly = shapely.wkt.loads('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (15 15, 15 20, 20 20, 20 15, 15 15))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(len(validated_poly) == 2)
        output_results.append({'properties': {'name': 'hole_outside_shell'}, 'geometry': mapping(validated_poly)})

        # This fails.
        print("Testing nested holes...")
        test_poly = shapely.wkt.loads('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (2 2, 2 8, 8 8, 8 2, 2 2), '
                                      '(3 3, 3 7, 7 7, 7 3, 3 3))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(len(validated_poly) == 2)
        output_results.append({'properties': {'name': 'nested_holes'}, 'geometry': mapping(validated_poly)})

        print("Testing disconnected interior...")
        test_poly = shapely.wkt.loads('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (5 0, 10 5, 5 10, 0 5, 5 0))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(len(validated_poly) == 4)
        output_results.append({'properties': {'name': 'disconnected_interior'}, 'geometry': mapping(validated_poly)})

        print("Testing ring self-intersection...")
        test_poly = shapely.wkt.loads('POLYGON((5 0, 10 0, 10 10, 0 10, 0 0, 5 0, 3 3, 5 6, 7 3, 5 0))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertIsInstance(validated_poly, Polygon)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(len(validated_poly.interiors) == 1)
        output_results.append({'properties': {'name': 'ring_self_intersection'}, 'geometry': mapping(validated_poly)})

        print("Testing nested shells...")
        test_poly = shapely.wkt.loads('MULTIPOLYGON(((0 0, 10 0, 10 10, 0 10, 0 0)),(( 2 2, 8 2, 8 8, 2 8, 2 2)))')
        validated_poly = makevalid.make_geom_valid(test_poly)
        self.assertIsInstance(validated_poly, Polygon)
        self.assertTrue(validated_poly.is_valid)
        self.assertTrue(validated_poly.area == 64.0)
        output_results.append({'properties': {'name': 'nested_shells'}, 'geometry': mapping(validated_poly)})

        # TODO: Write out the output results if you like?

if __name__ == '__main__':
        unittest.main()
