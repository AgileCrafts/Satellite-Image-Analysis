import React from 'react';
import MapGL, { NavigationControl } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MapPage = () => {
  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <MapGL
        width="100%"
        height="100%"
        latitude={23.5657}
        longitude={90.5356}
        zoom={12}
        mapStyle="mapbox://styles/mapbox/streets-v11"
        mapboxApiAccessToken="YOUR_MAPBOX_TOKEN"
      >
        <NavigationControl style={{ top: 10, left: 10 }} />
      </MapGL>
    </div>
  );
};

export default MapPage;
