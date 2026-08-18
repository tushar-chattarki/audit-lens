import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { NewReviewPage } from './pages/NewReviewPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { OverviewPage } from './pages/OverviewPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { FindingsPage } from './pages/FindingsPage';
import { EvidencePage } from './pages/EvidencePage';
import { WP514Page } from './pages/WP514Page';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/review/new" replace />} />
          <Route path="review/new" element={<NewReviewPage />} />
          <Route path="review/:jobId/processing" element={<ProcessingPage />} />
          <Route path="review/:jobId/overview" element={<OverviewPage />} />
          <Route path="review/:jobId/analysis" element={<AnalyticsPage />} />
          <Route path="review/:jobId/findings" element={<FindingsPage />} />
          <Route path="review/:jobId/evidence/:evidenceId" element={<EvidencePage />} />
          <Route path="review/:jobId/wp514" element={<WP514Page />} />
          <Route path="*" element={<Navigate to="/review/new" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
