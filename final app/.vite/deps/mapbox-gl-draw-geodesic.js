import {
  mapbox_gl_draw_default
} from "./chunk-KS5GD76W.js";
import "./chunk-7WLGYQZ4.js";
import {
  __commonJS,
  __toESM
} from "./chunk-V4OQ3NZ2.js";

// node_modules/hat/index.js
var require_hat = __commonJS({
  "node_modules/hat/index.js"(exports, module) {
    var hat2 = module.exports = function(bits, base) {
      if (!base) base = 16;
      if (bits === void 0) bits = 128;
      if (bits <= 0) return "0";
      var digits = Math.log(Math.pow(2, bits)) / Math.log(base);
      for (var i = 2; digits === Infinity; i *= 2) {
        digits = Math.log(Math.pow(2, bits / i)) / Math.log(base) * i;
      }
      var rem = digits - Math.floor(digits);
      var res = "";
      for (var i = 0; i < Math.floor(digits); i++) {
        var x = Math.floor(Math.random() * base).toString(base);
        res = x + res;
      }
      if (rem) {
        var b = Math.pow(base, rem);
        var x = Math.floor(Math.random() * b).toString(base);
        res = x + res;
      }
      var parsed = parseInt(res, base);
      if (parsed !== Infinity && parsed >= Math.pow(2, bits)) {
        return hat2(bits, base);
      } else return res;
    };
    hat2.rack = function(bits, base, expandBy) {
      var fn = function(data) {
        var iters = 0;
        do {
          if (iters++ > 10) {
            if (expandBy) bits += expandBy;
            else throw new Error("too many ID collisions, use more bits");
          }
          var id = hat2(bits, base);
        } while (Object.hasOwnProperty.call(hats, id));
        hats[id] = data;
        return id;
      };
      var hats = fn.hats = {};
      fn.get = function(id) {
        return fn.hats[id];
      };
      fn.set = function(id, value) {
        fn.hats[id] = value;
        return fn;
      };
      fn.bits = bits || 128;
      fn.base = base || 16;
      return fn;
    };
  }
});

// node_modules/arc/arc.js
var require_arc = __commonJS({
  "node_modules/arc/arc.js"(exports, module) {
    "use strict";
    var D2R = Math.PI / 180;
    var R2D = 180 / Math.PI;
    var Coord = function(lon, lat) {
      this.lon = lon;
      this.lat = lat;
      this.x = D2R * lon;
      this.y = D2R * lat;
    };
    var roundCoords = function(coords) {
      var PRECISION = 6;
      var MULTIPLIER = Math.pow(10, PRECISION);
      for (var i = 0; i < coords.length; i++) {
        coords[i] = Math.round(
          (coords[i] + Number.EPSILON) * MULTIPLIER
        ) / MULTIPLIER;
      }
      return coords;
    };
    Coord.prototype.view = function() {
      return String(this.lon).slice(0, 4) + "," + String(this.lat).slice(0, 4);
    };
    Coord.prototype.antipode = function() {
      var anti_lat = -1 * this.lat;
      var anti_lon = this.lon < 0 ? 180 + this.lon : (180 - this.lon) * -1;
      return new Coord(anti_lon, anti_lat);
    };
    var LineString = function() {
      this.coords = [];
      this.length = 0;
    };
    LineString.prototype.move_to = function(coord) {
      this.length++;
      this.coords.push(coord);
    };
    var Arc = function(properties2) {
      this.properties = properties2 || {};
      this.geometries = [];
    };
    Arc.prototype.json = function() {
      if (this.geometries.length <= 0) {
        return {
          "geometry": { "type": "LineString", "coordinates": null },
          "type": "Feature",
          "properties": this.properties
        };
      } else if (this.geometries.length == 1) {
        return {
          "geometry": { "type": "LineString", "coordinates": this.geometries[0].coords },
          "type": "Feature",
          "properties": this.properties
        };
      } else {
        var multiline = [];
        for (var i = 0; i < this.geometries.length; i++) {
          multiline.push(this.geometries[i].coords);
        }
        return {
          "geometry": { "type": "MultiLineString", "coordinates": multiline },
          "type": "Feature",
          "properties": this.properties
        };
      }
    };
    Arc.prototype.wkt = function() {
      var wkt_string = "";
      var wkt = "LINESTRING(";
      var collect = function(c) {
        wkt += c[0] + " " + c[1] + ",";
      };
      for (var i = 0; i < this.geometries.length; i++) {
        if (this.geometries[i].coords.length === 0) {
          return "LINESTRING(empty)";
        } else {
          var coords = this.geometries[i].coords;
          coords.forEach(collect);
          wkt_string += wkt.substring(0, wkt.length - 1) + ")";
        }
      }
      return wkt_string;
    };
    var GreatCircle = function(start, end, properties2) {
      if (!start || start.x === void 0 || start.y === void 0) {
        throw new Error("GreatCircle constructor expects two args: start and end objects with x and y properties");
      }
      if (!end || end.x === void 0 || end.y === void 0) {
        throw new Error("GreatCircle constructor expects two args: start and end objects with x and y properties");
      }
      this.start = new Coord(start.x, start.y);
      this.end = new Coord(end.x, end.y);
      this.properties = properties2 || {};
      var w = this.start.x - this.end.x;
      var h = this.start.y - this.end.y;
      var z = Math.pow(Math.sin(h / 2), 2) + Math.cos(this.start.y) * Math.cos(this.end.y) * Math.pow(Math.sin(w / 2), 2);
      this.g = 2 * Math.asin(Math.sqrt(z));
      if (this.g == Math.PI) {
        throw new Error("it appears " + this.start.view() + " and " + this.end.view() + " are 'antipodal', e.g diametrically opposite, thus there is no single route but rather infinite");
      } else if (isNaN(this.g)) {
        throw new Error("could not calculate great circle between " + start + " and " + end);
      }
    };
    GreatCircle.prototype.interpolate = function(f) {
      var A = Math.sin((1 - f) * this.g) / Math.sin(this.g);
      var B = Math.sin(f * this.g) / Math.sin(this.g);
      var x = A * Math.cos(this.start.y) * Math.cos(this.start.x) + B * Math.cos(this.end.y) * Math.cos(this.end.x);
      var y = A * Math.cos(this.start.y) * Math.sin(this.start.x) + B * Math.cos(this.end.y) * Math.sin(this.end.x);
      var z = A * Math.sin(this.start.y) + B * Math.sin(this.end.y);
      var lat = R2D * Math.atan2(z, Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2)));
      var lon = R2D * Math.atan2(y, x);
      return [lon, lat];
    };
    GreatCircle.prototype.Arc = function(npoints, options) {
      var first_pass = [];
      if (!npoints || npoints <= 2) {
        first_pass.push([this.start.lon, this.start.lat]);
        first_pass.push([this.end.lon, this.end.lat]);
      } else {
        var delta = 1 / (npoints - 1);
        for (var i = 0; i < npoints; ++i) {
          var step = delta * i;
          var pair = this.interpolate(step);
          first_pass.push(pair);
        }
      }
      var bHasBigDiff = false;
      var dfMaxSmallDiffLong = 0;
      var dfDateLineOffset = options && options.offset ? options.offset : 10;
      var dfLeftBorderX = 180 - dfDateLineOffset;
      var dfRightBorderX = -180 + dfDateLineOffset;
      var dfDiffSpace = 360 - dfDateLineOffset;
      for (var j = 1; j < first_pass.length; ++j) {
        var dfPrevX = first_pass[j - 1][0];
        var dfX = first_pass[j][0];
        var dfDiffLong = Math.abs(dfX - dfPrevX);
        if (dfDiffLong > dfDiffSpace && (dfX > dfLeftBorderX && dfPrevX < dfRightBorderX || dfPrevX > dfLeftBorderX && dfX < dfRightBorderX)) {
          bHasBigDiff = true;
        } else if (dfDiffLong > dfMaxSmallDiffLong) {
          dfMaxSmallDiffLong = dfDiffLong;
        }
      }
      var poMulti = [];
      if (bHasBigDiff && dfMaxSmallDiffLong < dfDateLineOffset) {
        var poNewLS = [];
        poMulti.push(poNewLS);
        for (var k = 0; k < first_pass.length; ++k) {
          var dfX0 = parseFloat(first_pass[k][0]);
          if (k > 0 && Math.abs(dfX0 - first_pass[k - 1][0]) > dfDiffSpace) {
            var dfX1 = parseFloat(first_pass[k - 1][0]);
            var dfY1 = parseFloat(first_pass[k - 1][1]);
            var dfX2 = parseFloat(first_pass[k][0]);
            var dfY2 = parseFloat(first_pass[k][1]);
            if (dfX1 > -180 && dfX1 < dfRightBorderX && dfX2 == 180 && k + 1 < first_pass.length && first_pass[k - 1][0] > -180 && first_pass[k - 1][0] < dfRightBorderX) {
              poNewLS.push([-180, first_pass[k][1]]);
              k++;
              poNewLS.push([first_pass[k][0], first_pass[k][1]]);
              continue;
            } else if (dfX1 > dfLeftBorderX && dfX1 < 180 && dfX2 == -180 && k + 1 < first_pass.length && first_pass[k - 1][0] > dfLeftBorderX && first_pass[k - 1][0] < 180) {
              poNewLS.push([180, first_pass[k][1]]);
              k++;
              poNewLS.push([first_pass[k][0], first_pass[k][1]]);
              continue;
            }
            if (dfX1 < dfRightBorderX && dfX2 > dfLeftBorderX) {
              var tmpX = dfX1;
              dfX1 = dfX2;
              dfX2 = tmpX;
              var tmpY = dfY1;
              dfY1 = dfY2;
              dfY2 = tmpY;
            }
            if (dfX1 > dfLeftBorderX && dfX2 < dfRightBorderX) {
              dfX2 += 360;
            }
            if (dfX1 <= 180 && dfX2 >= 180 && dfX1 < dfX2) {
              var dfRatio = (180 - dfX1) / (dfX2 - dfX1);
              var dfY = dfRatio * dfY2 + (1 - dfRatio) * dfY1;
              poNewLS.push([first_pass[k - 1][0] > dfLeftBorderX ? 180 : -180, dfY]);
              poNewLS = [];
              poNewLS.push([first_pass[k - 1][0] > dfLeftBorderX ? -180 : 180, dfY]);
              poMulti.push(poNewLS);
            } else {
              poNewLS = [];
              poMulti.push(poNewLS);
            }
            poNewLS.push([dfX0, first_pass[k][1]]);
          } else {
            poNewLS.push([first_pass[k][0], first_pass[k][1]]);
          }
        }
      } else {
        var poNewLS0 = [];
        poMulti.push(poNewLS0);
        for (var l = 0; l < first_pass.length; ++l) {
          poNewLS0.push([first_pass[l][0], first_pass[l][1]]);
        }
      }
      var arc3 = new Arc(this.properties);
      for (var m = 0; m < poMulti.length; ++m) {
        var line = new LineString();
        arc3.geometries.push(line);
        var points = poMulti[m];
        for (var j0 = 0; j0 < points.length; ++j0) {
          line.move_to(roundCoords(points[j0]));
        }
      }
      return arc3;
    };
    if (typeof module !== "undefined" && typeof module.exports !== "undefined") {
      module.exports.Coord = Coord;
      module.exports.Arc = Arc;
      module.exports.GreatCircle = GreatCircle;
    } else {
      arc2 = {};
      arc2.Coord = Coord;
      arc2.Arc = Arc;
      arc2.GreatCircle = GreatCircle;
    }
    var arc2;
  }
});

// node_modules/arc/index.js
var require_arc2 = __commonJS({
  "node_modules/arc/index.js"(exports, module) {
    module.exports = require_arc();
  }
});

// node_modules/mapbox-gl-draw-geodesic/dist/mapbox-gl-draw-geodesic.esm.js
var import_hat = __toESM(require_hat());
var import_arc = __toESM(require_arc2());

// node_modules/geodesy-fn/dist/geodesy-fn.js
var DEFAULT_RADIUS = 6371e3;
function equals(position1, position2) {
  if (Math.abs(position1[0] - position2[0]) > Number.EPSILON)
    return false;
  if (Math.abs(position1[1] - position2[1]) > Number.EPSILON)
    return false;
  return true;
}
function toRadians(value) {
  return value / 180 * Math.PI;
}
function toDegrees(value) {
  return value / Math.PI * 180;
}
function wrap360(value) {
  return (value + 360) % 360;
}
function distance(start, destination, radius = DEFAULT_RADIUS) {
  const R = radius;
  const φ1 = toRadians(start[1]), λ1 = toRadians(start[0]);
  const φ2 = toRadians(destination[1]), λ2 = toRadians(destination[0]);
  const Δφ = φ2 - φ1;
  const Δλ = λ2 - λ1;
  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const d = R * c;
  return d;
}
function initialBearing(start, destination) {
  if (equals(start, destination))
    return NaN;
  const φ1 = toRadians(start[1]);
  const φ2 = toRadians(destination[1]);
  const Δλ = toRadians(destination[0] - start[0]);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  const y = Math.sin(Δλ) * Math.cos(φ2);
  const θ = Math.atan2(y, x);
  const bearing = toDegrees(θ);
  return wrap360(bearing);
}
function midpoint(start, destination) {
  const φ1 = toRadians(start[1]);
  const λ1 = toRadians(start[0]);
  const φ2 = toRadians(destination[1]);
  const Δλ = toRadians(destination[0] - start[0]);
  const A = { x: Math.cos(φ1), y: 0, z: Math.sin(φ1) };
  const B = { x: Math.cos(φ2) * Math.cos(Δλ), y: Math.cos(φ2) * Math.sin(Δλ), z: Math.sin(φ2) };
  const C = { x: A.x + B.x, y: A.y + B.y, z: A.z + B.z };
  const φm = Math.atan2(C.z, Math.sqrt(C.x * C.x + C.y * C.y));
  const λm = λ1 + Math.atan2(C.y, C.x);
  const lat = toDegrees(φm);
  const lon = toDegrees(λm);
  return [lon, lat];
}
function destinationPoint(start, distance3, bearing, radius = DEFAULT_RADIUS) {
  const δ = distance3 / radius;
  const θ = toRadians(bearing);
  const φ1 = toRadians(start[1]), λ1 = toRadians(start[0]);
  const sinφ2 = Math.sin(φ1) * Math.cos(δ) + Math.cos(φ1) * Math.sin(δ) * Math.cos(θ);
  const φ2 = Math.asin(sinφ2);
  const y = Math.sin(θ) * Math.sin(δ) * Math.cos(φ1);
  const x = Math.cos(δ) - Math.sin(φ1) * sinφ2;
  const λ2 = λ1 + Math.atan2(y, x);
  const lat = toDegrees(φ2);
  const lon = toDegrees(λ2);
  return [lon, lat];
}

// node_modules/mapbox-gl-draw-geodesic/dist/mapbox-gl-draw-geodesic.esm.js
var {
  cursors,
  geojsonTypes,
  events,
  meta,
  activeStates
} = mapbox_gl_draw_default.constants;
var modes = {
  ...mapbox_gl_draw_default.constants.modes,
  DRAW_CIRCLE: "draw_circle"
};
var properties = {
  CIRCLE_RADIUS: "circleRadius",
  CIRCLE_HANDLE_BEARING: "circleHandleBearing"
};
function createCircle(center, radius) {
  let properties$1 = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : {};
  if (!(radius > 0)) {
    throw new Error("Radius has to be greater then 0");
  }
  return {
    id: (0, import_hat.default)(),
    type: geojsonTypes.FEATURE,
    properties: {
      [properties.CIRCLE_RADIUS]: radius,
      // km
      ...properties$1
    },
    geometry: {
      type: geojsonTypes.POLYGON,
      coordinates: [[center, center, center, center]]
      // valid polygon needs 3 vertices
    }
  };
}
function isCircleByTypeAndProperties(type, properties$1) {
  return type === geojsonTypes.POLYGON && typeof properties$1[properties.CIRCLE_RADIUS] === "number" && properties$1[properties.CIRCLE_RADIUS] > 0;
}
function isCircle(geojson) {
  return isCircleByTypeAndProperties(geojson.geometry.type, geojson.properties);
}
function getCircleCenter(geojson) {
  if (!isCircle(geojson)) {
    throw new Error("GeoJSON is not a circle");
  }
  return geojson.geometry.coordinates[0][0];
}
function setCircleCenter(geojson, center) {
  if (!isCircle(geojson)) {
    throw new Error("GeoJSON is not a circle");
  }
  geojson.geometry.coordinates = [[center, center, center, center]];
}
function getCircleRadius(geojson) {
  if (!isCircle(geojson)) {
    throw new Error("GeoJSON is not a circle");
  }
  return geojson.properties[properties.CIRCLE_RADIUS];
}
function setCircleRadius(geojson, radius) {
  if (!isCircle(geojson)) {
    throw new Error("GeoJSON is not a circle");
  }
  geojson.properties[properties.CIRCLE_RADIUS] = radius;
}
function coordinatesEqual(x, y) {
  return x[0] === y[0] && x[1] === y[1];
}
function coordinatePairs(array) {
  return array.slice(0, -1).map((value, index) => [value, array[index + 1]]).filter((pair) => !coordinatesEqual(pair[0], pair[1]));
}
function createGeodesicLine(coordinates) {
  let steps = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 32;
  const segments = coordinatePairs(coordinates);
  const geodesicSegments = segments.map((segment) => {
    const greatCircle = new import_arc.default.GreatCircle({
      x: segment[0][0],
      y: segment[0][1]
    }, {
      x: segment[1][0],
      y: segment[1][1]
    });
    return greatCircle.Arc(steps, {
      offset: 90
    }).json();
  });
  let worldOffset = 0;
  const geodesicCoordinates = geodesicSegments.map((geodesicSegment) => {
    if (geodesicSegment.geometry.type === geojsonTypes.MULTI_LINE_STRING) {
      const prevWorldOffset = worldOffset;
      const nextWorldOffset = worldOffset + (geodesicSegment.geometry.coordinates[0][0][0] > geodesicSegment.geometry.coordinates[1][0][0] ? 1 : -1);
      const geodesicCoordinates2 = [...geodesicSegment.geometry.coordinates[0].map((x) => [x[0] + prevWorldOffset * 360, x[1]]), ...geodesicSegment.geometry.coordinates[1].map((x) => [x[0] + nextWorldOffset * 360, x[1]])];
      worldOffset = nextWorldOffset;
      return geodesicCoordinates2;
    } else {
      const geodesicCoordinates2 = geodesicSegment.geometry.coordinates.map((x) => [x[0] + worldOffset * 360, x[1]]);
      return geodesicCoordinates2;
    }
  }).flat();
  return geodesicCoordinates.filter((coord, index) => index === geodesicCoordinates.length - 1 || !coordinatesEqual(coord, geodesicCoordinates[index + 1]));
}
var DEFAULT_RADIUS2 = 6371.0088;
function distance2(start, destination) {
  return distance(start, destination, DEFAULT_RADIUS2);
}
function destinationPoint2(start, distance3, bearing) {
  return destinationPoint(start, distance3, bearing, DEFAULT_RADIUS2);
}
function createGeodesicCircle(center, radius, bearing, steps) {
  const coordinates = [];
  for (let i = 0; i < steps; ++i) {
    coordinates.push(destinationPoint2(center, radius, bearing + 360 * -i / steps));
  }
  coordinates.push(coordinates[0]);
  return coordinates;
}
var STEPS = 32;
var HANDLE_BEARING = 45;
function isCircleFeature(feature) {
  return isCircleByTypeAndProperties(feature.type, feature.properties);
}
function getMidpointStartCoordPath(path) {
  return path.split(".").map((x, i, array) => i === array.length - 1 ? (parseInt(x, 10) - 1).toString() : x).join(".");
}
function getMidpointEndCoordPath(feature, path) {
  if (feature.type === geojsonTypes.POLYGON || feature.type === geojsonTypes.MULTI_POLYGON) {
    try {
      feature.getCoordinate(path);
      return path;
    } catch (e) {
      return path.split(".").map((x, i, array) => i === array.length - 1 ? "0" : x).join(".");
    }
  } else {
    return path;
  }
}
function createGeodesicGeojson(geojson, options) {
  options = {
    steps: STEPS,
    ...options
  };
  const properties$1 = geojson.properties;
  const type = geojson.geometry.type;
  const coordinates = geojson.geometry.coordinates;
  const featureId = properties$1.parent || properties$1.id;
  const feature = options.ctx.store.get(featureId);
  if (type === geojsonTypes.POINT) {
    if (isCircleFeature(feature)) {
      return [];
    } else if (properties$1.meta === meta.MIDPOINT) {
      return processMidpoint();
    } else {
      return [geojson];
    }
  } else if (type === geojsonTypes.LINE_STRING) {
    return processLine();
  } else if (type === geojsonTypes.POLYGON) {
    if (isCircleFeature(feature)) {
      return processCircle();
    } else {
      return processPolygon();
    }
  } else if (type.indexOf(geojsonTypes.MULTI_PREFIX) === 0) {
    return processMultiGeometry();
  }
  function isSelectedPath(path) {
    if (!options.selectedPaths) {
      return false;
    }
    return options.selectedPaths.indexOf(path) !== -1;
  }
  function processMidpoint() {
    const coordPath = properties$1.coord_path;
    const startCoordPath = getMidpointStartCoordPath(coordPath);
    const endCoordPath = getMidpointEndCoordPath(feature, coordPath);
    const startCoord = feature.getCoordinate(startCoordPath);
    const endCoord = feature.getCoordinate(endCoordPath);
    const midCoord = midpoint(startCoord, endCoord);
    const geodesicGeojson = {
      ...geojson,
      properties: {
        ...properties$1,
        lng: midCoord[0],
        lat: midCoord[1]
      },
      geometry: {
        ...geojson.geometry,
        coordinates: midCoord
      }
    };
    return [geodesicGeojson];
  }
  function processLine() {
    const geodesicCoordinates = createGeodesicLine(coordinates, options.steps);
    const geodesicGeojson = {
      ...geojson,
      geometry: {
        ...geojson.geometry,
        coordinates: geodesicCoordinates
      }
    };
    return [geodesicGeojson];
  }
  function processPolygon() {
    const geodesicCoordinates = coordinates.map((subCoordinates) => {
      return createGeodesicLine(subCoordinates);
    });
    const geodesicGeojson = {
      ...geojson,
      geometry: {
        ...geojson.geometry,
        coordinates: geodesicCoordinates
      }
    };
    return [geodesicGeojson];
  }
  function processCircle() {
    const featureGeojson = feature.toGeoJSON();
    const center = getCircleCenter(featureGeojson);
    const radius = getCircleRadius(featureGeojson);
    const handleBearing = feature[properties.CIRCLE_HANDLE_BEARING] || HANDLE_BEARING;
    const geodesicCoordinates = createGeodesicCircle(center, radius, handleBearing, options.steps * 4);
    const geodesicGeojson = {
      ...geojson,
      geometry: {
        ...geojson.geometry,
        coordinates: [geodesicCoordinates]
      }
    };
    if (properties$1.active === activeStates.ACTIVE) {
      const handle = destinationPoint2(center, radius, handleBearing);
      const points = [center, handle];
      const vertices = points.map((point, i) => {
        return mapbox_gl_draw_default.lib.createVertex(properties$1.id, point, `0.${i}`, isSelectedPath(`0.${i}`));
      });
      return [geodesicGeojson, ...vertices];
    } else {
      return [geodesicGeojson];
    }
  }
  function processMultiGeometry() {
    const subType = type.replace(geojsonTypes.MULTI_PREFIX, "");
    const geodesicFeatures = coordinates.map((subCoordinates) => {
      const subFeature = {
        type: geojsonTypes.FEATURE,
        properties: properties$1,
        geometry: {
          type: subType,
          coordinates: subCoordinates
        }
      };
      return createGeodesicGeojson(subFeature, options);
    }).flat();
    const geodesicCoordinates = geodesicFeatures.map((subFeature) => {
      return subFeature.geometry.coordinates;
    });
    const geodesicGeojson = {
      ...geojson,
      geometry: {
        ...geojson.geometry,
        coordinates: geodesicCoordinates
      }
    };
    return [geodesicGeojson];
  }
}
function patchDrawLineString(DrawLineString) {
  const DrawLineStringPatched = {
    ...DrawLineString
  };
  DrawLineStringPatched.toDisplayFeatures = function(state, geojson, display) {
    const displayGeodesic = (geojson2) => {
      const geodesicGeojson = createGeodesicGeojson(geojson2, {
        ctx: this._ctx
      });
      geodesicGeojson.forEach(display);
    };
    DrawLineString.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };
  return DrawLineStringPatched;
}
function patchDrawPolygon(DrawPolygon) {
  const DrawPolygonPatched = {
    ...DrawPolygon
  };
  DrawPolygonPatched.toDisplayFeatures = function(state, geojson, display) {
    const displayGeodesic = (geojson2) => {
      const geodesicGeojson = createGeodesicGeojson(geojson2, {
        ctx: this._ctx
      });
      geodesicGeojson.forEach(display);
    };
    DrawPolygon.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };
  return DrawPolygonPatched;
}
var dragPan = {
  enable(ctx) {
    setTimeout(() => {
      if (!ctx.map || !ctx.map.dragPan || !ctx._ctx || !ctx._ctx.store || !ctx._ctx.store.getInitialConfigValue) return;
      if (!ctx._ctx.store.getInitialConfigValue("dragPan")) return;
      ctx.map.dragPan.enable();
    }, 0);
  },
  disable(ctx) {
    setTimeout(() => {
      if (!ctx.map || !ctx.map.doubleClickZoom) return;
      ctx.map.dragPan.disable();
    }, 0);
  }
};
var DrawCircleGeodesic = {};
DrawCircleGeodesic.onSetup = function(opts) {
  this.clearSelectedFeatures();
  mapbox_gl_draw_default.lib.doubleClickZoom.disable(this);
  dragPan.disable(this);
  this.updateUIClasses({
    mouse: cursors.ADD
  });
  this.setActionableState();
  return {};
};
DrawCircleGeodesic.onMouseDown = DrawCircleGeodesic.onTouchStart = function(state, e) {
  const center = [e.lngLat.lng, e.lngLat.lat];
  const circle = this.newFeature(createCircle(center, Number.EPSILON));
  this.addFeature(circle);
  state.circle = circle;
};
DrawCircleGeodesic.onDrag = DrawCircleGeodesic.onTouchMove = function(state, e) {
  if (state.circle) {
    const geojson = state.circle.toGeoJSON();
    const center = getCircleCenter(geojson);
    const handle = [e.lngLat.lng, e.lngLat.lat];
    const radius = distance2(center, handle);
    const handleBearing = initialBearing(center, handle);
    state.circle.properties[properties.CIRCLE_RADIUS] = radius;
    state.circle[properties.CIRCLE_HANDLE_BEARING] = handleBearing;
    state.circle.changed();
  }
};
DrawCircleGeodesic.onMouseUp = DrawCircleGeodesic.onTouchEnd = function(state, e) {
  this.map.fire(events.CREATE, {
    features: [state.circle.toGeoJSON()]
  });
  return this.changeMode(modes.SIMPLE_SELECT, {
    featureIds: [state.circle.id]
  });
};
DrawCircleGeodesic.onKeyUp = function(state, e) {
  if (mapbox_gl_draw_default.lib.CommonSelectors.isEscapeKey(e)) {
    if (state.circle) {
      this.deleteFeature([state.circle.id], {
        silent: true
      });
    }
    this.changeMode(modes.SIMPLE_SELECT);
  } else if (mapbox_gl_draw_default.lib.CommonSelectors.isEnterKey(e)) {
    this.changeMode(modes.SIMPLE_SELECT, {
      featureIds: [state.circle.id]
    });
  }
};
DrawCircleGeodesic.onStop = function() {
  this.updateUIClasses({
    mouse: cursors.NONE
  });
  mapbox_gl_draw_default.lib.doubleClickZoom.enable(this);
  dragPan.enable(this);
  this.activateUIButton();
};
DrawCircleGeodesic.toDisplayFeatures = function(state, geojson, display) {
  if (state.circle) {
    const isActivePolygon = geojson.properties.id === state.circle.id;
    geojson.properties.active = isActivePolygon ? activeStates.ACTIVE : activeStates.INACTIVE;
  }
  const displayGeodesic = (geojson2) => {
    const geodesicGeojson = createGeodesicGeojson(geojson2, {
      ctx: this._ctx
    });
    geodesicGeojson.forEach(display);
  };
  displayGeodesic(geojson);
};
function patchDrawPoint(DrawPoint) {
  const DrawPointPatched = {
    ...DrawPoint
  };
  DrawPointPatched.toDisplayFeatures = function(state, geojson, display) {
    const displayGeodesic = (geojson2) => {
      const geodesicGeojson = createGeodesicGeojson(geojson2, {
        ctx: this._ctx
      });
      geodesicGeojson.forEach(display);
    };
    DrawPoint.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };
  return DrawPointPatched;
}
function patchSimpleSelect(SimpleSelect) {
  const SimpleSelectPatched = {
    ...SimpleSelect
  };
  SimpleSelectPatched.toDisplayFeatures = function(state, geojson, display) {
    const displayGeodesic = (geojson2) => {
      const geodesicGeojson = createGeodesicGeojson(geojson2, {
        ctx: this._ctx
      });
      geodesicGeojson.forEach(display);
    };
    SimpleSelect.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };
  return SimpleSelectPatched;
}
function patchDirectSelect(DirectSelect) {
  const DirectSelectPatched = {
    ...DirectSelect
  };
  DirectSelectPatched.dragVertex = function(state, e, delta) {
    const geojson = state.feature.toGeoJSON();
    if (isCircle(geojson)) {
      if (state.selectedCoordPaths[0] === "0.1") {
        const center = getCircleCenter(geojson);
        const handle = [e.lngLat.lng, e.lngLat.lat];
        const radius = distance2(center, handle);
        const handleBearing = initialBearing(center, handle);
        state.feature.properties[properties.CIRCLE_RADIUS] = radius;
        state.feature[properties.CIRCLE_HANDLE_BEARING] = handleBearing;
        state.feature.changed();
      } else {
        DirectSelect.dragFeature.call(this, state, e, delta);
      }
    } else {
      DirectSelect.dragVertex.call(this, state, e, delta);
    }
  };
  DirectSelectPatched.toDisplayFeatures = function(state, geojson, display) {
    const displayGeodesic = (geojson2) => {
      const geodesicGeojson = createGeodesicGeojson(geojson2, {
        ctx: this._ctx,
        selectedPaths: state.selectedCoordPaths
      });
      geodesicGeojson.forEach(display);
    };
    DirectSelect.toDisplayFeatures.call(this, state, geojson, displayGeodesic);
  };
  return DirectSelectPatched;
}
var StaticGeodesic = {};
StaticGeodesic.onSetup = function() {
  this.setActionableState();
  return {};
};
StaticGeodesic.toDisplayFeatures = function(state, geojson, display) {
  const displayGeodesic = (geojson2) => {
    const geodesicGeojson = createGeodesicGeojson(geojson2, {
      ctx: this._ctx
    });
    geodesicGeojson.forEach(display);
  };
  displayGeodesic(geojson);
};
function enable(modes$1) {
  return {
    ...modes$1,
    [modes.DRAW_LINE_STRING]: patchDrawLineString(modes$1[modes.DRAW_LINE_STRING]),
    [modes.DRAW_POLYGON]: patchDrawPolygon(modes$1[modes.DRAW_POLYGON]),
    [modes.DRAW_CIRCLE]: DrawCircleGeodesic,
    [modes.DRAW_POINT]: patchDrawPoint(modes$1[modes.DRAW_POINT]),
    [modes.SIMPLE_SELECT]: patchSimpleSelect(modes$1[modes.SIMPLE_SELECT]),
    [modes.DIRECT_SELECT]: patchDirectSelect(modes$1[modes.DIRECT_SELECT]),
    [modes.STATIC]: StaticGeodesic
  };
}
export {
  createCircle,
  enable,
  getCircleCenter,
  getCircleRadius,
  isCircle,
  isCircleByTypeAndProperties,
  setCircleCenter,
  setCircleRadius
};
//# sourceMappingURL=mapbox-gl-draw-geodesic.js.map
