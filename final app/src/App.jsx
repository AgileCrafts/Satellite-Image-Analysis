import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import MapPage from './pages/MapPage';
import Dashboard from './pages/Dashboard';
import Register from './pages/Register';
import MainLayout from './pages/MainLayout';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ports" element={< Dashboard/>}/>
          <Route path="/encroachments" element={<MapPage />} />
          {/* <Route path="/map/view" element={<MapPage />} />
          <Route path="/map/changemap" element={<ChangeMap />} /> */}
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
