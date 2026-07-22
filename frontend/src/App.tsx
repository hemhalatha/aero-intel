import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { RootLayout } from './layouts/RootLayout';
import { CommandCenter } from './pages/CommandCenter';
import { Investigation } from './pages/Investigation';
import { Attribution } from './pages/Attribution';
import { ScenarioSimulation } from './pages/ScenarioSimulation';
import { Recommendations } from './pages/Recommendations';
import { TaskManagement } from './pages/TaskManagement';
import { Accountability } from './pages/Accountability';
import { CitizenAdvisory } from './pages/CitizenAdvisory';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<CommandCenter />} />
          <Route path="investigation" element={<Investigation />} />
          <Route path="attribution" element={<Attribution />} />
          <Route path="simulation" element={<ScenarioSimulation />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="tasks" element={<TaskManagement />} />
          <Route path="accountability" element={<Accountability />} />
          <Route path="advisory" element={<CitizenAdvisory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;