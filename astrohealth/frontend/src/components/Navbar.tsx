import React, { useState } from 'react';
import { 
  Activity, 
  ShieldAlert, 
  Cpu, 
  Wind, 
  Heart, 
  UserCheck, 
  LogOut, 
  Radio, 
  ChevronDown,
  AlertTriangle,
  Bell,
  Menu,
  X
} from 'lucide-react';
import { User, UserRole } from '../types';
import { authApi } from '../services/api';

interface NavbarProps {
  currentUser: User | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onLoginClick: (role: UserRole) => void;
  onEmergencyClick: () => void;
  onAlertCenterClick: () => void;
  onLogout: () => void;
  activeAlertCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  onLoginClick,
  onEmergencyClick,
  onAlertCenterClick,
  onLogout,
  activeAlertCount = 0
}) => {
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleTabSelect = (tab: string) => {
    setActiveTab(tab);
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 bg-space-950/85 backdrop-blur-md border-b border-space-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Mission Code */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-cyan-glow">
              <Activity className="w-6 h-6 text-space-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-wider text-white">ASTROHEALTH</span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                  Ares-V
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block tracking-wide">
                Intelligent Health Monitoring Beyond Earth
              </p>
            </div>
          </div>

          {/* Navigation Links - Desktop */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => handleTabSelect('astronaut')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'astronaut'
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-space-850'
              }`}
            >
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Astronaut Dashboard</span>
            </button>

            <button
              onClick={() => handleTabSelect('medical')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'medical'
                  ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-space-850'
              }`}
            >
              <UserCheck className="w-4 h-4 text-blue-400" />
              <span>Medical Officer Hub</span>
            </button>

            <button
              onClick={() => handleTabSelect('environmental')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'environmental'
                  ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-space-850'
              }`}
            >
              <Wind className="w-4 h-4 text-emerald-400" />
              <span>Cabin Life Support</span>
            </button>

            <button
              onClick={() => handleTabSelect('wellness')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'wellness'
                  ? 'bg-violet-500/15 text-violet-300 border border-violet-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-space-850'
              }`}
            >
              <Heart className="w-4 h-4 text-violet-400" />
              <span>Psychological Wellness</span>
            </button>

            <button
              onClick={() => handleTabSelect('simulator')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center space-x-1.5 ${
                activeTab === 'simulator'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-space-850'
              }`}
            >
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>IoT Simulator</span>
            </button>
          </nav>

          {/* Right Action Area */}
          <div className="flex items-center space-x-2 sm:space-x-3">

            {/* Alert Center Trigger */}
            <button
              onClick={onAlertCenterClick}
              className="relative p-2 rounded-lg bg-space-900 hover:bg-space-850 text-slate-300 hover:text-white border border-space-800 transition"
              title="Mission Health & Safety Alerts"
            >
              <Bell className="w-4 h-4" />
              {activeAlertCount > 0 && (
                <span className="absolute -top-1 -right-1 px-1.5 py-0.2 rounded-full text-[10px] font-black bg-rose-600 text-white animate-pulse">
                  {activeAlertCount}
                </span>
              )}
            </button>
            
            {/* Emergency SOS Button */}
            <button
              onClick={onEmergencyClick}
              className="px-2.5 py-1.5 rounded bg-red-600/80 hover:bg-red-500 text-white font-mono text-xs font-bold transition-all shadow-alert-glow flex items-center space-x-1.5 animate-pulse"
              title="Broadcast Manual Crew Medical Alert"
            >
              <AlertTriangle className="w-4 h-4" />
              <span className="hidden sm:inline">EMERGENCY SOS</span>
            </button>

            {/* Quick Demo Switcher / User Profile */}
            <div className="relative">
              {currentUser ? (
                <div className="flex items-center space-x-2 bg-space-900 border border-space-800 rounded-lg p-1.5 pr-2.5">
                  <div className="w-7 h-7 rounded-full bg-cyan-900/60 border border-cyan-700/50 flex items-center justify-center text-xs font-mono font-bold text-cyan-300">
                    {currentUser.callsign ? currentUser.callsign.substring(0, 2) : currentUser.username.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="text-left hidden lg:block">
                    <p className="text-xs font-semibold text-white leading-tight">{currentUser.full_name}</p>
                    <p className="text-[10px] text-cyan-400 font-mono capitalize">{currentUser.role.replace('_', ' ')}</p>
                  </div>
                  <button 
                    onClick={() => setShowRoleMenu(!showRoleMenu)}
                    className="text-slate-400 hover:text-white"
                  >
                    <ChevronDown className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowRoleMenu(!showRoleMenu)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-space-950 font-bold text-xs transition-all flex items-center space-x-1"
                >
                  <span>Select Role Login</span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>
              )}

              {/* Role Selection Dropdown Menu */}
              {showRoleMenu && (
                <div className="absolute right-0 mt-2 w-64 rounded-lg bg-space-900 border border-space-700 shadow-panel py-2 z-50 text-xs">
                  <div className="px-3 py-1.5 border-b border-space-800 text-[11px] text-slate-400 font-mono uppercase">
                    Switch Active Crew Role:
                  </div>
                  <button
                    onClick={() => { onLoginClick('astronaut'); setShowRoleMenu(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-space-800 flex items-center justify-between text-slate-200"
                  >
                    <div>
                      <p className="font-semibold text-white">Cmdr. Alex Novak</p>
                      <p className="text-[10px] text-cyan-400">Astronaut (Pioneer-1)</p>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-space-800 text-slate-400">Crew</span>
                  </button>
                  <button
                    onClick={() => { onLoginClick('medical_officer'); setShowRoleMenu(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-space-800 flex items-center justify-between text-slate-200"
                  >
                    <div>
                      <p className="font-semibold text-white">Dr. Marcus Vance, MD</p>
                      <p className="text-[10px] text-blue-400">Chief Medical Officer</p>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-space-800 text-slate-400">Medical</span>
                  </button>
                  <button
                    onClick={() => { onLoginClick('admin'); setShowRoleMenu(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-space-800 flex items-center justify-between text-slate-200"
                  >
                    <div>
                      <p className="font-semibold text-white">Elena Rostova</p>
                      <p className="text-[10px] text-amber-400">Mission Administrator</p>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-space-800 text-slate-400">Admin</span>
                  </button>
                  {currentUser && (
                    <div className="mt-1 pt-1 border-t border-space-800">
                      <button
                        onClick={() => { onLogout(); setShowRoleMenu(false); }}
                        className="w-full text-left px-3 py-1.5 text-red-400 hover:bg-space-800 flex items-center space-x-2"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Mobile Hamburger Menu Toggle Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-lg bg-space-900 border border-space-800 text-slate-300 hover:text-white transition"
              title="Toggle Navigation Menu"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5 text-cyan-400" /> : <Menu className="w-5 h-5" />}
            </button>

          </div>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-space-800 bg-space-950/95 backdrop-blur-lg px-4 pt-3 pb-5 space-y-1">
          <button
            onClick={() => handleTabSelect('astronaut')}
            className={`w-full px-3 py-2.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2.5 ${
              activeTab === 'astronaut'
                ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-bold'
                : 'text-slate-300 hover:bg-space-900'
            }`}
          >
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Astronaut Dashboard</span>
          </button>

          <button
            onClick={() => handleTabSelect('medical')}
            className={`w-full px-3 py-2.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2.5 ${
              activeTab === 'medical'
                ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30 font-bold'
                : 'text-slate-300 hover:bg-space-900'
            }`}
          >
            <UserCheck className="w-4 h-4 text-blue-400" />
            <span>Medical Officer Hub</span>
          </button>

          <button
            onClick={() => handleTabSelect('environmental')}
            className={`w-full px-3 py-2.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2.5 ${
              activeTab === 'environmental'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold'
                : 'text-slate-300 hover:bg-space-900'
            }`}
          >
            <Wind className="w-4 h-4 text-emerald-400" />
            <span>Cabin Life Support</span>
          </button>

          <button
            onClick={() => handleTabSelect('wellness')}
            className={`w-full px-3 py-2.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2.5 ${
              activeTab === 'wellness'
                ? 'bg-violet-500/15 text-violet-300 border border-violet-500/30 font-bold'
                : 'text-slate-300 hover:bg-space-900'
            }`}
          >
            <Heart className="w-4 h-4 text-violet-400" />
            <span>Psychological Wellness</span>
          </button>

          <button
            onClick={() => handleTabSelect('simulator')}
            className={`w-full px-3 py-2.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-2.5 ${
              activeTab === 'simulator'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold'
                : 'text-slate-300 hover:bg-space-900'
            }`}
          >
            <Cpu className="w-4 h-4 text-amber-400" />
            <span>IoT Simulator</span>
          </button>
        </div>
      )}
    </header>
  );
};

