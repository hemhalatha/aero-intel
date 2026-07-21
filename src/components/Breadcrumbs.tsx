import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  return (
    <div className="flex items-center space-x-2 text-xs text-gray-400 font-mono py-2 px-6 bg-dark-800/50 border-b border-dark-700">
      <Link to="/" className="hover:text-brand-cyan flex items-center gap-1">
        <Home className="h-3 w-3" />
        <span>AEROINTEL</span>
      </Link>
      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        return (
          <React.Fragment key={name}>
            <ChevronRight className="h-3 w-3 text-gray-600" />
            {isLast ? (
              <span className="text-brand-cyan uppercase font-bold">{name}</span>
            ) : (
              <Link to={routeTo} className="hover:text-white uppercase">
                {name}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};