import React, { useState, useEffect } from 'react';
import { User, UserRole } from './types';
import { Navbar } from './components/Navbar';
import { EmergencyModal } from './components/EmergencyModal';
import { AlertCenterModal } from './components/AlertCenterModal';
import { AstronautDashboard } from './pages/AstronautDashboard';
import { MedicalOfficerDashboard } from './pages/MedicalOfficerDashboard';
import { EnvironmentalDashboard } from './pages/EnvironmentalDashboard';
import { WellnessPage } from './pages/WellnessPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { authApi } from './services/api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<string>('astronaut');
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);
  const [isAlertCenterOpen, setIsAlertCenterOpen] = useState<boolean>(false);
  const [activeAlertCount, setActiveAlertCount] = useState<number>(0);
  const [activeAstronautId, setActiveAstronautId] = useState<string>('ASTRO-001');

  // Automatic initial login to demonstrate immediate operational system
  useEffect(() => {
    const initAuth = async () => {
      const stored = authApi.getCurrentUser();
      if (stored) {
        setCurrentUser(stored);
      } else {
        // Default login as Mission Commander Alex Novak
        try {
          const res = await authApi.login('astro_alex', 'AstroPassword123!');
          setCurrentUser(res.user);
        } catch (e) {
          console.error('Initial login fallback:', e);
        }
      }
    };
    initAuth();
  }, []);

  const handleRoleQuickLogin = async (role: UserRole) => {
    try {
      if (role === 'astronaut') {
        const res = await authApi.login('astro_alex', 'AstroPassword123!');
        setCurrentUser(res.user);
        setActiveAstronautId('ASTRO-001');
        setActiveTab('astronaut');
      } else if (role === 'medical_officer') {
        const res = await authApi.login('dr_vance', 'DoctorPassword123!');
        setCurrentUser(res.user);
        setActiveTab('medical');
      } else if (role === 'admin') {
        const res = await authApi.login('admin', 'AdminPassword123!');
        setCurrentUser(res.user);
        setActiveTab('simulator');
      }
    } catch (err) {
      console.error('Role quick login error:', err);
    }
  };

  const handleLogout = () => {
    authApi.logout();
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen bg-space-950 text-slate-100 flex flex-col font-sans">
      {/* Top Aerospace Mission Navbar */}
      <Navbar
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLoginClick={handleRoleQuickLogin}
        onEmergencyClick={() => setIsEmergencyModalOpen(true)}
        onAlertCenterClick={() => setIsAlertCenterOpen(true)}
        onLogout={handleLogout}
        activeAlertCount={activeAlertCount}
      />

      {/* Main View Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-12">
        {activeTab === 'astronaut' && (
          <AstronautDashboard
            astronautId={activeAstronautId}
            onEmergencyClick={() => setIsEmergencyModalOpen(true)}
            onAstronautChange={setActiveAstronautId}
          />
        )}

        {activeTab === 'simulator' && (
          <SimulatorPage />
        )}

        {activeTab === 'medical' && (
          <MedicalOfficerDashboard />
        )}

        {activeTab === 'environmental' && (
          <EnvironmentalDashboard />
        )}

        {activeTab === 'wellness' && (
          <WellnessPage />
        )}
      </main>

      {/* Emergency Modal */}
      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        astronautId={activeAstronautId}
      />

      {/* Alert Center Modal */}
      <AlertCenterModal
        isOpen={isAlertCenterOpen}
        onClose={() => setIsAlertCenterOpen(false)}
        onAlertCountChange={setActiveAlertCount}
      />
    </div>
  );
};

