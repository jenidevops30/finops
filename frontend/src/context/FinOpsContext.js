import React, { createContext, useContext, useState, useEffect } from 'react';

const FinOpsContext = createContext();

export const useFinOps = () => {
  const context = useContext(FinOpsContext);
  if (!context) {
    throw new Error('useFinOps must be used within a FinOpsProvider');
  }
  return context;
};

export const FinOpsProvider = ({ children }) => {
  // Dark Mode State
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? saved === 'true' : false;
  });

  // Account & Region Filters
  const [selectedAccount, setSelectedAccount] = useState(() => {
    return localStorage.getItem('selectedAccount') || 'all';
  });

  const [selectedRegion, setSelectedRegion] = useState(() => {
    return localStorage.getItem('selectedRegion') || 'all';
  });

  // Default accounts and regions (will be enriched dynamically or static)
  const accounts = [
    { id: 'all', name: 'All Accounts' },
    { id: '123456789012', name: '123456789012 (Prod)' },
    { id: '987654321098', name: '987654321098 (Dev)' }
  ];

  const regions = [
    { id: 'all', name: 'All Regions' },
    { id: 'us-east-1', name: 'us-east-1 (N. Virginia)' },
    { id: 'us-west-2', name: 'us-west-2 (Oregon)' },
    { id: 'ap-south-1', name: 'ap-south-1 (Mumbai)' }
  ];

  // Sync dark mode class with HTML tag
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  // Persist filters
  useEffect(() => {
    localStorage.setItem('selectedAccount', selectedAccount);
  }, [selectedAccount]);

  useEffect(() => {
    localStorage.setItem('selectedRegion', selectedRegion);
  }, [selectedRegion]);

  const toggleDarkMode = () => {
    setDarkMode(prev => !prev);
  };

  return (
    <FinOpsContext.Provider
      value={{
        darkMode,
        toggleDarkMode,
        selectedAccount,
        setSelectedAccount,
        selectedRegion,
        setSelectedRegion,
        accounts,
        regions
      }}
    >
      {children}
    </FinOpsContext.Provider>
  );
};
