import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import MapPage from './pages/MapPage';
import Dashboard from './pages/Dashboard';
import Register from './pages/Register';
import MainLayout from './pages/MainLayout';
import ChangeMap from './pages/ChangeMap';
import MergedMapPage from './pages/MergedMap';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/map" element={<MergedMapPage />} />
          {/* <Route path="/map/view" element={<MapPage />} />
          <Route path="/map/changemap" element={<ChangeMap />} /> */}
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
